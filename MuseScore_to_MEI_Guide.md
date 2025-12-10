# CRIM: MuseScore to MEI

Last Update:  December 2025

- Guidelines for Editors preparing MuseScore Files
- Exporting from MuseScore to MEI 
- Post Processing with [MEI Tools](https://github.com/RichardFreedman/mei_tools/blob/main/README.md)  

## Table of Contents

- [Authors](#authors)
- [What are MEI Tools?](#what-are-mei-tools)
- [Preparing MuseScore Editions for MEI: Engraving and "E" Files!](#preparing-sibelius-editions-for-mei-engraving-and-e-files)
- [MusicXML to MEI with MuseScore](#musicxml-to-mei-with-musescore)
- [CRIM Style Sheet for MuseScore MEI Export](#style-sheets-for-musescore-mei-export)
- [Metadata](#metadata)
- [Staves, Instrument Types, and Voice Names](#staves)
- [Clefs](#clefs)
- [Incipits + Measure Numbers](#incipits--measure-numbers)
- [First + Second Endings](#first--second-endings)
- [Original Note Values and Time Signatures](#time-signatures)
- [Rests in 3/1 Bars](#rests-in-31-bars)
- [Accidentals + Musica ficta](#accidentals--musica-ficta)
- [Sib to MEI to Verovio](#sib-to-mei-to-verovio)
- [Final longa](#final-longa)
- [Ligatures + Coloration](#ligatures--coloration)
- [Metronome markings](#metronome-markings)
- [Lyrics](#lyrics)

## Author

- Richard Freedman (Haverford College, USA)


## What are MEI Tools?

- [MEI Tools](https://github.com/RichardFreedman/mei_tools/blob/main/README.md) are a set of Python scripts that transform the flat MEI files produced by `sibmei` or `MuseScore` as rich MEI files.   
- MEI Tools are modular:  various functions can be included/excluded depending on the required output. These include:
- editing metadata
- removing and correcting music features such as inicipts, lyrics, musica ficta, etc.
- In [The Lost Voices Project](digitalduchemin.org), several related staves in flat MEI became single staves in rich MEI, using a combination of details already present in the original Sibelius file to determine the encoding.
- In [Citations:  The Renaissance Imitation Mass (CRIM)](crimproject.org) the rich encoding is limited mainly to musica ficta, which is marked in red in the Sibelius, but massaged as <supplied> in the MEI


## Preparing MuseScore Editions for MEI: Engraving and "E" Files!

- In this guide we describe the best practices for preparing MuseScore files for export to MEI, and subsequent processing with MEI Tools to produce rich MEI files suitable for analysis and digital editions. 


<!-- Review these -->
### The key steps include:
 - **initial import** from MusicXML to MuseScore
 - **apply CRIM Style Sheet** for MuseScore MEI Export (using MuseScore `Format > Style` menu; get the style sheet from this repository)
 - **add metadata**, including composer, title, and copyright information (using MuseScore `File > Project properties` menu); these will be included in the exported MEI file (which we nevertheless can curate further with MEI Tools as needed)
    - note that the **copyright** information will display in the MuseScore notation and PDF. But in order to display the **composer** and **title**, you will need to add these as text objects in the MuseScore file (using MuseScore `Add > Text > Title` and `Add > Text > Composer` menus)
 - **rename parts** (double click on staff name in MuseScore, then select `Vocal > [appropriate voice]` from the dropdown menu and rename as needed)   
 - **update clefs** according to range of each part (using MuseScore `Palettes > Clefs` menus)
 - **remove incipit and confirm first measure** = `1`
 - **adjust durations** to match original notational values (`select all notes/rests in score`, then `Edit > copy`, then MuseScore `Edit > Paste double duration`), as needed.
    - Note if your piece has **more than one time signature**, you will to do this in sections rather than the entire score at once.  You will need to: 
        - 1) **count the number of measures in that section** then 
        - 2) `select` the last bar in that section, and 
        - 3) `add` that number of empty measures to the end of the section using MuseScore `Add > Measures > Insert after selection`.  
        - 4) `copy` all the notes in the original section and then `Edit > paste double duration`.  
    - Be sure to review the entire section to ensure that all durations are correct, then move on to the next step (set the time signature for that section)
 - **reset time signatures** to match actual count of notational values in each bar (`select` the given time signature, use MuseScore `Palettes > Time Signatures` menu). 
 - **hide time signatures** as needed for engraving (`right click or Alt`, then adjust `Time Signature Properties`), while retaining correct underlying time signature for MEI export
 - **correct rhythmic groupings and stem directions** as needed (`select all notes/rests in score`, then MuseScore `Tools > regroup rhythms`), as needed.
 - **review accidentals; encode musica ficta and color notes that require musica ficta** (for ficta + color: add the addicdental on the staff, then select the note and use MuseScore Plug-in `Musica_ficta_color` to color the note red and move the accidental above the staff; consider creating a custom keyboard shortcut for this plug-in)
 - **add or correct lyrics**, including second verses as needed (`select` the first note of the second verse, then MuseScore `Add > Lyrics Line 2`, then enter syllables as needed)
- **export to MEI** using MuseScore `File > Export` menu, selecting `MEI` as the file type.  Note that we can also do this for a corpus of files with a command-line script using `mscore` (see [MuseScore Command Line Export](https://musescore.org/en/handbook/command-line-export) for details)
- **export to PDF** for engraving using MuseScore `File > Export` menu, selecting `PDF` as the file type.  Note that we can also do this with a command-line script using `mscore` (see [MuseScore Command Line Export](https://musescore.org/en/handbook/command-line-export) for details)

As a subsequent step, we will process the exported MEI files with [MEI Tools](https://github.com/RichardFreedman/mei_tools/blob/main/README.md) in order to correctly format the MEI files for analysis and digital editions.  This includes adding metadata, correcting lyrics with elisions, and encoding musica ficta as `<supplied>` elements.  



## Preparing MuseScore Editions for MEI:  One File Does It All!

- Unlike the process for Sibelius files, MuseScore does not require separate "E" files for MEI export.  The same MuseScore file can be used both for engraving (PDF export) and for MEI export.

## Details of the Steps Mentioned Above

- The following sections provide more details and screenshots for the key steps mentioned above.

### Importing from MusicXML to MuseScore

- This is done using MuseScore `File > Open` menu, selecting the MusicXML file as the source.
- Alternatively, you can drag and drop the MusicXML file onto the MuseScore application icon or window.

### Applying CRIM Style Sheet for MuseScore MEI Export

- Download the `CRIM Style Sheet` for MuseScore from this repository.
- In MuseScore, use the `Format > Load Style` menu to import and apply the style sheet to your score.
- This ensures that the engraved PDF file adheres to CRIM conventions.

Open the `Format > Load Style` menu:

<br>

> <details>
> <summary>Show Image</summary>
> <img src="images/ms_load_style.png" alt="Format Load Style menu" />
>
> </details>

<br>

And now 'apply' the style sheet to this score:

<br>

> <details>
> <summary>Show Image</summary>
> <img src="images/ms_load_style2.png" alt="Style applied" />
>
> </details>

<br>

### Adding Metadata in MuseScore

- Use MuseScore `File > Project Properties` menu to add **composer, title, and copyright** information.
- These will be included in the exported MEI file (which we nevertheless can curate further with MEI Tools as needed)

- Sample copyright content:

    `© Centre d'études supérieures de la Renaissance | Haverford College | Heidelberg University | The CRIM Project (crimproject.org)\`

Click below to see the `Project Properties` menu:

<br>

> <details>
> <summary>Show Image</summary>
> <img src="images/MS_metadata.png" alt="Project Properties" />
>
> </details>

<br>

Note that the **copyright** information will display in the MuseScore notation and PDF. But in order to display the **composer** and **title**, you will need to add these as **text objects** in the MuseScore file (using MuseScore `Add > Text > Title` and `Add > Text > Composer` menus), as shown below in the next section.



### Add Composer and Title Text Objects in MuseScore
- Use MuseScore `Add > Text > Title` and `Add > Text > Composer` menus to add text objects for composer and title in the score.
- This ensures that the composer and title are visible in the MuseScore notation and PDF export.

<br>

> <details>
> <summary>Show Image</summary>
> <img src="images/MS_comp_title.png" alt="Composer and Title" />
>
> </details>

<br>

Enter the title and composer in the respective text objects:

<br>

> <details>
> <summary>Show Image</summary>
> <img src="images/MS_title.png" alt="Title Entry" />
>
> </details>

<br>

The final result will look like this:

<br>

> <details>
> <summary>Show Image</summary>
> <img src="images/MS_finalComp_title.png" alt="Final Composer and Title" />
>
> </details>

<br>


## Staves

- Make sure the vocal parts are correctly named.  Normally these will follow the original source.
    - If the source does not provide a name for a given part, use “[  ]” to indicate an unnamed part.
    - If the source gives two voices the same name (for instance, two "Tenor" parts), then distinguish them as "Tenor [1]" and "Tenor [2]".
- To change the part name in MuseScore, **double click on the staff name**, then use the **replace instrument** button to select an appropriate part name from the **vocals** section.
- You can then edit the display name to match the original source.  The 'long instrument name' will be used on the first staff; the  'short instrument name' will be used on subsequent staves.
    - Remember that each part name should be **unique** within the score.  This will ensure that the MEI export correctly distinguishes between different parts.  So if you have two Tenor parts, be sure to rename them as "Tenor [1]" and "Tenor [2]" (or similar).

The first staff dialogue in MuseScore looks like this, and is where you can edit the display name:

<br>

> <details>
> <summary>Show Image</summary>
> <img src="images/ms_staff_1.png" alt="First staff dialogue" />
>
> </details>

<br>

Here is the second dialogue, where you can select the vocal part type:

<br>

> <details>
> <summary>Show Image</summary>
> <img src="images/muse_staff_2.png" />
>
> </details>

<br>

## Clefs

- Make sure the clef for each part matches the range of that part.
- To change the clef in MuseScore, first **select the clef you want to change**, then use the `Palettes > Clefs`
- In MuseScore, unlike Sibelius, the G8va clef will export correctly to MEI, with the appropriate octave shift.

Now the staff is renamed:

<br>

> <details>
> <summary>Show Image</summary>
> <img src="images/MS_clefs.png"  />
>
> </details>

</br>

## Incipits + Measure Numbers

- In the CRIM Project we do not include incipits in the PDF.  But if you want to include one for other purposes incipit (if you use one) must be a separate bar, and must be numbered "0". incipit = bar 0, first true measure = bar 1
- MEI Tools provides module to retain or remove incipit
- The bar numbers in the original MuseScore file determine those retained in the MEI file during sibmei export
- For Mass movements:  use **continuous bar numbers for each movement** (Kyrie, Christe, and Kyrie should be a single file with continous bar numbers)

## First + Second Endings

- In MuseScore First and second endings are created with `Palettes > Repeats and Jumps`

## Adjusting Durations and Time Signatures to Match Original Notational Values

### Double the Durations

- CRIM uses **unreduced note values**
- If your MusicXML import has reduced note values, you will need to double the durations of all notes and rests to match the original notational values.  Here is how to do this in MuseScore:
    - `select all notes/rests in score` (Ctrl + A or Cmd + A)
    - `Edit > copy` (Ctrl + C or Cmd + C)
    - MuseScore `Edit > Paste double duration` (Ctrl + Shift + V or Cmd + Shift + V)
- Important: if your piece has **more than one time signature**, you will to do this in sections rather than the entire score at once.  You will need to: 
    - 1) **count the number of measures in the section for a given time signature** then 
    - 2) `select` the last bar in that section, and 
    - 3) `add` that number of empty measures to the end of the section using MuseScore `Add > Measures > Insert` after selection.  
    - 4) `copy` all the notes in the original section and then `Edit > paste double duration`.  
- Be sure to review the entire section to ensure that all durations are correct, then move on to the next step ("Correct the Time Signatures")
- Note that after this step you will also want to reset the rhytyhmic groupings and stem directions after adjusting durations (see below).

### Correct the Time Signatures

- After adjusting durations, you will need to **reset the time signatures to match the actual count of notational values in each bar**.
- Normally you will have bars like `4/2` and `3/1`, which will correspond to `Cut C` and `3` in the original source.
- To do this in MuseScore, **select** the given time signature, then use MuseScore `Palettes > Time Signatures` menu to set the correct time signature.

Here is the Time Signatures palette in MuseScore:

<br>


> <details>
> <summary>Show Image</summary>
> <img src="images/MS_Time-Sig.png"  />
>
> </details>

</br>


- Note that if you have **multiple time signatures** in your piece, you will need to do this for **each section** separately, as noted above in `Double the Durations`.
- MEI Tools and MEI Tools record the time signatures as  **meter.unit** and **meter.count** attributes as part of the `scoreDef` and `staffDef` elements.  Having these correctly recorded (and corresponding to the actual count of beats in each measure) ensures that CRIM Intervals will correctly understand and analyize durations. 
- As explained below, you can nevertheless hide time signatures as needed for PDF engraving while retaining the correct underlying time signature for MEI export.


### Hide/Show Time Signatures for Engraving

- In CRIM, our policy is to display `Cut C` (alla breve) and `3` in the engraved PDF output, even as the underlying MEI file encodes these bars as `4/2` and `3/1`.  
    - As noted above, this is required for correct rhythmic interpretation with CRIM Intervals.  Verovio renderings of the MEI will also display the time signatures as `4/2` and `3/1`.
- Here is how to do this in MuseScore:
    - **right click (or Alt + click) on the time signature**, then adjust the `Time Signature Properties` to 'cover' it with a new symbol, such as `Cut C` or `3`.  The underlying actual meter will not be effected by this change, but the engraved PDF will display the desired symbol.
 


Select a time signature to 'cover' for engraving


<br>


> <details>
> <summary>Show Image</summary>
> <img src="images/ms_ts_hide_1.png"  />
>
> </details>

</br>

And now select the desired symbol to cover the time signature:


<br>


> <details>
> <summary>Show Image</summary>
> <img src="images/ms_ts_hide_2.png"  />
>
> </details>

</br>

The final result will look like this in the engraved PDF:


<br>


> <details>
> <summary>Show Image</summary>
> <img src="images/ms_ts_hide_3.png"  />
>
> </details>

</br>


### Reset Rhythmic Groupings and Stem Directions as Needed



MuseScore provides a tool to reset rhythmic groupings and stem directions after adjusting durations.  Tied notes within a bar will be grouped together (as longer values or dotted notes), and stem directions will be set according to standard engraving conventions.

To do this in MuseScore:
- `select all notes/rests in score` (Ctrl + A or Cmd + A)
- then use MuseScore `Format > reset shapes and positions` menu.

See below for screenshots of this process.

<br>

> <details>
> <summary>Show Image</summary>
> <img src="images/MS_stem_1.png" alt="Final Composer and Title" />
>
> </details>

<br>

And now the result after resetting shapes and positions:

<br>

> <details>
> <summary>Show Image</summary>
> <img src="images/MS_stem_2.png" alt="Final Composer and Title" />
>
> </details>

<br>


## Review Accidentals; Encode Musica ficta and Color Ficta Notes 

Accidentals that appear in the original sources are recorded without special editorial commentary in our transcriptions.  Simply click the notehead in question and use the MuseScore `Palettes > Accidentals` menu to add the appropriate accidental, or simply use the main toolbar, as shown here:


<br>

> <details>
> <summary>Show Image</summary>
> <img src="images/ms_accid_1.png" alt="Final Composer and Title" />
>
> </details>

<br>

But other accidentals are **editorially supplied` to indicate musica ficta.  In CRIM these are recorded in red above the staff, and are exported to MEI as `<supplied>` elements.  In order to and encode these correctly in MuseScore, we use the following procedure, which will color the effected note red and move the accidental above the staff.  MEI tools will then convert these to `<supplied>` elements in the MEI file.

Here is now to do this in MuseScore:

- Make sure you have added the Musica_ficta_color plug-in to MuseScore.  You can download it from th MEI Tools github repository.

- For each note that requires musica ficta:
    - add the accidental on the staff using MuseScore `Palettes > Accidentals` menu or the main toolbar
    - select the note with the accidental
    - use MuseScore Plug-in `Musica_ficta_color` to color the note red and move the accidental above the staff
    - consider creating a custom keyboard shortcut for this plug-in to speed up the process.

The process will look like this:

<br>

> <details>
> <summary>Show Image</summary>
> <img src="images/ms_accid_2.png" alt="Final Composer and Title" />
>
> </details>

<br>

And the result like this:

<br>

> <details>
> <summary>Show Image</summary>
> <img src="images/ms_accid_3.png" alt="Final Composer and Title" />
>
> </details>

<br>




## Add or Correct Lyrics


<!-- review this! -->
Carefully add lyrics to the score using MuseScore `Add > Text > Lyrics` menu. 

CRIM editions follow standard editorial practice for Renaissance music: 



- Be sure to encode second verse (if required) as “lyrics line 2”. If both sets of lyrics are encoded as Lyric 1, they will collide in meiView. (The results of sibmei and MEIMassaging will nevertheless be valid.)
- Be sure that each syllable is attached to a note (and never to a rest or barline). Syllables attached to rests or barlines will produce invalid MEI files after sibmei.
- Elisions (for instance between `ky-ri-e_e-le-i_son`) will be engraved by Sibelius with a small curving line.  Sib MEI exports these in a way that creates TWO syllables for a given note.  We correct these with MEI Tools to display as two syllables connected by an underscore (`_`)

<!-- get image for lyrics -->

## MuseScore to MEI and PDF


<!-- get image for MEI and PDF export -->


## Final longa

- In CRIM the final tone is entered in Sibelius as a longa (via the keypad).
- The extra line to create the longa is added as a symbol (line) for purposes of engraving. It does not export to MEI.
- In Du Chemin:  MEIMassaging converts final breve to final longa for purposes of the master MEI file.
- meiView nevertheless renders this as a breve in the present development.

<!-- check this and get image if needed -->

- sibmei export produces breve: `<note dur="breve" oct="3" pname="d" >`

- MEIMassaging produces longa: `<note oct="3" pname="d" dur="long">`

![Final Longa](images/image_14.png)




## Ligatures + Coloration

- Brackets used to indicate ligatures or coloration for engraved version are exported to MEI as annotations <annot>.
- These can be preserved or removed as with MEI Tools
- They are not supported in the current Verovio development



## Delete Metronome markings

- delete them (but they are not displayed in Verovio)


![Metronome Markings](images/image_17.png)



