import QtQuick 2.0
import MuseScore 3.0
MuseScore {
    menuPath: "Plugins.MusicaFictaColor"
    description: "Place editorial accidentals (musica ficta) above the staff and color selected notes red."
    version: "1.8"
    
    //4.4 title: "MusicaFictaColor"
    //4.4 categoryCode: "composing-arranging-tools"
    Component.onCompleted : {
        if (mscoreMajorVersion >= 4 && mscoreMinorVersion <= 3) {
           title = qsTr("MusicaFicta") ;
           // thumbnailName = ".png";
           categoryCode = "composing-arranging-tools";
        }
    }
    
    function makeFicta(accidental) {
      var targetLine = -4; // -4 is two ledger lines above staff
      var origLine = accidental.parent.line;
      var targetOffsetY;
      if(origLine<1) { //avoid collision with notes high on the staff
            targetOffsetY = -2;
      } else {
            targetOffsetY = (targetLine-origLine)/2; // calculate the difference & convert to staff spaces
      }

      // calculate horizontal center, accounting for resizing the accidental to small
      var smallNoteRatio;
      if (accidental.small == 1) { //if already small
            smallNoteRatio = 1; // don't need to adjust X calculations
      } else {
            smallNoteRatio = curScore.style.value("smallNoteMag");
      }
      
      var accidentalPosX = (accidental.posX-accidental.offsetX)*smallNoteRatio; //account for prior X offset
      var accidentalWidth = accidental.bbox.width*smallNoteRatio;
      var noteWidth = accidental.parent.bbox.width;
      var targetOffsetX = (noteWidth-accidentalWidth)/2-accidentalPosX;
            
      //apply properties 
      accidental.small = 1; 
      accidental.offsetX = targetOffsetX;
      accidental.offsetY = targetOffsetY;
    } //end makeFicta function
    
    // New function to color note heads red
    function colorNoteRed(note) {
      if (note) {
        note.color = "#FF0000"; // Set note head to red
      }
    }
    
    onRun: {
      
            curScore.startCmd();
      
        var elementsList = curScore.selection.elements;
        //Make sure something is selected.
        if (elementsList.length==0) {
            console.log("No selection.");
        }
        else if (elementsList.length==1 && elementsList[0].name=="Note") { //if a single note is selected
            var note = elementsList[0];
            if (note.accidentalType == Accidental.NONE) { //if no accidental
                  console.log("No accidental on that note.");
                  // Still color the note red even without accidental
                  colorNoteRed(note);
            } else {
                  console.log("Processing the accidental of the selected note.");
                  makeFicta(note.accidental);
                  colorNoteRed(note);
            }
        } //end single note selection
        else {
            for (var i=0; i<elementsList.length; i++) {
                  var element = elementsList[i];
                  if (element.name == "Accidental") {
                        console.log("Processing Element",i,"as Accidental.");
                        makeFicta(element);
                        // Color the parent note red
                        colorNoteRed(element.parent);
                  } 
                  else if (element.name == "Note") {
                        console.log("Processing Element",i,"as Note.");
                        if (element.accidentalType != Accidental.NONE) {
                            makeFicta(element.accidental);
                        }
                        colorNoteRed(element);
                  }
                  else if (element.name == "Chord") {
                        console.log("Processing Element",i,"as Chord.");
                        // Process all notes in the chord
                        for (var j=0; j<element.notes.length; j++) {
                            var chordNote = element.notes[j];
                            if (chordNote.accidentalType != Accidental.NONE) {
                                makeFicta(chordNote.accidental);
                            }
                            colorNoteRed(chordNote);
                        }
                  }
                  else {
                        console.log("Element",i,"is",element.name,"type so we do nothing.");
                  }
            } //end element list loop
        } //end selection check
        
            curScore.endCmd();
         
        (typeof(quit) === 'undefined' ? Qt.quit : quit)()
            
    } //end onRun
}