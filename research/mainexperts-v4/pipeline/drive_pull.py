"""Fetch your authorized Drive corpus with OAuth, saving the canonical pull manifest."""
import argparse
import json
import os
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from shutil import copyfileobj
from time import sleep

FOLDER = "application/vnd.google-apps.folder"
SHEET = "application/vnd.google-apps.spreadsheet"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

def request(path, token, params=None):
    url = "https://www.googleapis.com/drive/v3/" + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization":"Bearer "+token}),timeout=120)

def inspect_folder(folder, region, token, seen=None):
    if seen is None:
        seen=set()
    if folder in seen:
        return
    seen.add(folder)
    page = None
    while True:
        opts = {"q": f"'{folder}' in parents and trashed=false", "pageSize": 100,
                "fields":"nextPageToken,incompleteSearch,files(id,name,mimeType,size,webViewLink,createdTime,modifiedTime)",
                "supportsAllDrives":"true", "includeItemsFromAllDrives":"true"}
        if page:
            opts["pageToken"] = page
        with request("files",token,opts) as f:
            data=json.load(f)
        if data.get("incompleteSearch"):
            raise RuntimeError(f"Drive incompleteSearch for {region}/{folder}")
        for record in data["files"]:
            ident = record["id"]
            if record["mimeType"] == FOLDER:
                yield from inspect_folder(ident,region,token,seen)
            else:
                yield {"id":ident,"region":region,"title":record["name"],"mime_type":record["mimeType"],
                       "size":record.get("size"), "url":record.get("webViewLink") or f"https://drive.google.com/file/d/{ident}/view",
                       "created_time":record.get("createdTime"), "modified_time":record.get("modifiedTime")}
        page = data.get("nextPageToken")
        if not page:
            return

def pull_one(source, token, intake):
    code = source["id"]
    native = source["mime_type"] == SHEET
    ext = ".xlsx" if native or source["mime_type"] == XLSX else ".csv"
    dest = intake/"raw"/(code+ext)
    report = intake/"manifests"/(code+".json")
    for attempt in range(3):
        try:
            if not dest.exists():
                params = {"mimeType":XLSX} if native else {"alt":"media","supportsAllDrives":"true"}
                with request("files/"+code+("/export" if native else ""),token,params) as down, dest.with_suffix(".part").open("wb") as out:
                    copyfileobj(down,out,length=1<<20)
                dest.with_suffix(".part").replace(dest)
            report.write_text(json.dumps({"id":code,"bytes":dest.stat().st_size,"path":str(dest.relative_to(intake))}))
            return True
        except (OSError, ValueError) as exc:
            report.write_text(json.dumps({"id":code,"error":str(exc)}))
            if attempt < 2:
                sleep(2**attempt)
    return False

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folders",type=Path,required=True)
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--workers",type=int,default=7)
    args=parser.parse_args()
    token=os.environ.get("MAINEXPERTS_DRIVE_ACCESS_TOKEN")
    if not token:
        parser.error("Set MAINEXPERTS_DRIVE_ACCESS_TOKEN with read access to the source folder")
    for subdir in ("raw","manifests"):
        (args.input/subdir).mkdir(parents=True,exist_ok=True)
    folders=json.loads(args.folders.read_text())
    items=[]
    listed=set()
    for region,ident in folders.items():
        if region=="ROOT":
            continue
        for source in inspect_folder(ident,region,token):
            if source["id"] not in listed:
                listed.add(source["id"]); items.append(source)
    (args.input/"inventory.json").write_text(json.dumps(items,ensure_ascii=False,indent=2))
    pending=[r for r in items if r["region"]!="ONTO" and r["mime_type"] in {"text/csv",SHEET,XLSX}]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        succeeded=sum(pool.map(lambda source: pull_one(source,token,args.input),pending))
    print(f"Pulled {succeeded}/{len(pending)}")
    if succeeded!=len(pending):
        raise SystemExit(2)

if __name__=="__main__":
    main()
