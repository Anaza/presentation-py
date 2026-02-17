import PPTX from 'nodejs-pptx';
import { data } from './data/data.js';
import fs from 'fs';

let pptx = new PPTX.Composer();
const sprintNumber = process.argv[2] ? parseInt(process.argv[2]) : 1;

await pptx.load(`./template/base.pptx`);

await pptx.compose(async pres => {
  // Add sprintNumber to the first slide
  pres.getSlide(1).addText(text => {
    text
      .value(sprintNumber.toString())
      .x(106)
      .y(302)
      .cx(40)
      .cy(40)
      .fontFace('Arial')
      .fontSize(14)
      .textColor('FFFFFF')
      .fontBold(true);
  });

  for (let i = 0; i < data.length; i++) {
    const slideData = data[i];
    await pres.addSlide(async slide => {
      // Add logo
      slide.addImage(image => {
        image
          .file(`./images/logo.png`)
          .x(870)
          .y(22)
          .cx(70)
          .cy(13);
      });

      // Add epic
      slide.addText(text => {
        text
          .value(slideData.epic)
          .x(25)
          .y(6)
          .cx(800)
          .cy(40)
          .fontFace('Play')
          .fontSize(18)
          .fontBold(true)
          .textColor('FFFFFF')
          .textAlign('left');
      });

      // Add title
      slide.addText(text => {
        text
          .value(slideData.title)
          .x(25)
          .y(50)
          .cx(880)
          .cy(60)
          .fontFace('Play')
          .fontSize(32)
          .textColor('FFFFFF')
          .textAlign('left');
      });

      // Add items
      const itemsText = slideData.items.map(item => `• ${item}`).join('\n');
      slide.addText(text => {
        text
          .bulletPoints(itemsText)
          .x(30)
          .y(130)
          .cx(450)
          .cy(400)
          .fontFace('Arial')
          .fontSize(14)
          .textColor('FFFFFF')
          .textAlign('left')
          .textVerticalAlign('top');
      });
    });
  }

  // Move second slide to the end
  pres.getSlide(2).moveTo(data.length + 2);
});

// Ensure result directory exists
fs.mkdirSync('./result', { recursive: true });

await pptx.save(`./result/sprint_${sprintNumber}.pptx`);
