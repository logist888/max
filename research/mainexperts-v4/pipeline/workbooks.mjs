import fs from "node:fs/promises";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const [inputPath, outputDir, previewDir] = process.argv.slice(2);
const payload = JSON.parse(await fs.readFile(inputPath, "utf8"));
const notes = [
  ["Модель доказательности", "D0 — нет подтверждения, D1 — информация, D2 — инструмент или персональный результат, D3 — коммерческий поиск. D4–D6 требуют дополнительных данных."],
  ["География", "Рынок поиска, страна учебного заведения и папка источника — самостоятельные поля. ZZ-RU — русскоязычные выгрузки без подтверждённой географии."],
  ["Частотность", "Показатель одного наблюдения в указанной системе и типе метрики. Повторные оценки одного запроса и разные поисковики не складываются."],
  ["Исходные фразы", "Листы с примерами содержат оригинал и идентификатор запроса. Для полной выборки используйте аналитическую базу и реестр наблюдений."],
  ["Покупка", "Целевые цифры CAC, конверсий и маржи устанавливаются только по результатам платного эксперимента."]
];
const accent = "#1D4F88";
const standardWidth = 136;
for (const [filename, section] of Object.entries(payload)) {
  const w = Workbook.create();
  const home = w.worksheets.add("Как читать");
  home.getRange("A1:B1").merge();
  home.getCell(0,0).values = [[`MainExperts v4.0 · ${section.title}`]];
  home.getRange("A1:B1").format = { fill: "#12345B", font: { name: "Golos Text", size: 17, bold: true, color: "#FFFFFF" }, rowHeight: 40, verticalAlignment:"center" };
  home.getRangeByIndexes(2,0,notes.length,2).values = notes;
  home.getRange("A3:B7").format = { font:{name:"Golos Text",size:11,color:"#163451"}, wrapText:true, verticalAlignment:"center", rowHeight:40 };
  home.getRange("A:A").format.columnWidthPx=175;
  home.getRange("B:B").format.columnWidthPx=680;
  home.showGridLines=false;
  for (const {name,rows} of section.sheets) {
    const sheet=w.worksheets.add(name);
    const width=rows[0].length;
    const height=rows.length;
    sheet.showGridLines=false;
    sheet.tabColor=accent;
    const rectangle=sheet.getRangeByIndexes(0,0,height,width);
    const sanitized = rows.map(row=>row.map(v=>typeof v==="string"&&v.startsWith("=") ? "'"+v:v));
    rectangle.values=sanitized;
    rectangle.format.font={name:"Golos Text",size:10,color:"#1D364F"};
    rectangle.format.verticalAlignment="center";
    sheet.getRangeByIndexes(0,0,1,width).format={
      fill:accent,font:{name:"Golos Text",bold:true,color:"#FFFFFF"},rowHeight:32,
      wrapText:true,verticalAlignment:"center"
    };
    for (let col=0;col<width;col++) {
      const key=rows[0][col];
      const values=rows.slice(1,100).map(r=>r[col]).filter(v=>typeof v==="string");
      const lengths=values.map(v=>v.length).sort((a,b)=>a-b);
      const expected=lengths[Math.floor(lengths.length*.82)]??15;
      const px=Math.max(102,Math.min(350,Math.max(key.length*6.5,expected*5.1,standardWidth)));
      sheet.getRangeByIndexes(0,col,height,1).format.columnWidthPx=px;
      if (height>1 && px>230) sheet.getRangeByIndexes(1,col,height-1,1).format.wrapText=true;
    }
    if (height>1) {
      const body=sheet.getRangeByIndexes(1,0,height-1,width);
      body.format.rowHeight= name==="Исходные фразы" ? 40 : 55;
      body.format.borders={insideHorizontal:{style:"hair",color:"#DDE7F1"}};
      if (height < 1500) {
        for (let row=2;row<height;row+=2) sheet.getRangeByIndexes(row,0,1,width).format.fill="#F0F5FB";
      }
    }
    sheet.freezePanes.freezeRows(1);
  }
  const file=await SpreadsheetFile.exportXlsx(w);
  await file.save(`${outputDir}/${filename}`);
  if(previewDir) {
    await fs.mkdir(previewDir,{recursive:true});
    const img=await w.render({sheetName:"Как читать",range:"A1:B7",scale:1.25});
    await fs.writeFile(`${previewDir}/${filename}.png`,new Uint8Array(await img.arrayBuffer()));
  }
  console.log(filename,section.sheets.map(s=>[s.name,s.rows.length-1]));
}
