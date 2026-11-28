import fs from "node:fs/promises";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const [input, output, preview] = process.argv.slice(2);
const config = JSON.parse(await fs.readFile(input, "utf8"));
const book = Workbook.create();
const ink = "#173451";
const blue = "#205888";
const navy = "#123457";
const pale = "#E8F1F9";

function display(x) {
  if (x === "" || x === undefined || x === null) return null;
  if (typeof x === "string" && /^[=+\-@]/.test(x)) return "'" + x;
  return x;
}

for (const [idx, tab] of config.entries()) {
  const ws = book.worksheets.add(tab.name);
  ws.tabColor = idx < 2 ? navy : blue;
  ws.showGridLines = false;
  const n = tab.headers.length;
  const top = ws.getRangeByIndexes(0,0,1,n);
  top.merge();
  ws.getCell(0,0).values = [[tab.title]];
  top.format = {fill:navy,font:{name:"Golos Text",bold:true,color:"#FFFFFF",size:15},rowHeight:35,verticalAlignment:"center"};
  const strip = ws.getRangeByIndexes(1,0,1,n);
  strip.merge();
  ws.getCell(1,0).values = [[tab.description]];
  strip.format = {fill:pale,font:{name:"Golos Text",color:ink,size:10},rowHeight:37,verticalAlignment:"center",wrapText:true};
  const header = ws.getRangeByIndexes(3,0,1,n);
  header.values = [tab.headers];
  for (let col=0;col<n;col++) {
    ws.getRangeByIndexes(0,col,Math.max(tab.rows.length+4,5),1).format.columnWidthPx =
      tab.widths?.[col] || 150;
  }
  for (let offset=0;offset<tab.rows.length;offset+=800) {
    const batch=tab.rows.slice(offset,offset+800).map(row=>row.map(display));
    ws.getRangeByIndexes(offset+4,0,batch.length,n).values=batch;
  }
  if (tab.rows.length>0) {
    const endColumn = String.fromCharCode(64+n);
    const table = ws.tables.add(`A4:${endColumn}${tab.rows.length+4}`, true, `P08Ledger${idx+1}`);
    table.style = "TableStyleMedium2";
    table.showFilterButton = true;
    if (tab.rows.length<6500) {
      const data=ws.getRangeByIndexes(4,0,tab.rows.length,n);
      data.format.font={name:"Golos Text",color:ink,size:10};
      data.format.wrapText=true;
      data.format.verticalAlignment="center";
      data.format.rowHeight=tab.rowHeight??29;
    }
  }
  header.format = {fill:blue,font:{name:"Golos Text",color:"#FFFFFF",bold:true,size:10},rowHeight:26,wrapText:true,verticalAlignment:"center"};
  ws.freezePanes.freezeRows(4);
  console.log(tab.name,tab.rows.length);
}

if (preview) {
  const img=await book.render({sheetName:config[0].name,range:"A1:D14",scale:1.1});
  await fs.writeFile(preview,new Uint8Array(await img.arrayBuffer()));
}
const out=await SpreadsheetFile.exportXlsx(book);
await out.save(output);
