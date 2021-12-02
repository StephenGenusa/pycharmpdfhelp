# PyCharm Web Help to PDF

- By Stephen Genusa [http://www.github.com/stephengenusa](http://www.github.com/stephengenusa)
- December 1, 2021
- Built using Python 3.9, Selenium and PyMuPDF

This program determines the latest release version of PyCharm help and builds a 
complete help file in PDF format including a full multi-level table of contents
that mirrors the original web content.

![PyCharm PDF Documentation with ToC](C:\Users\Stephen\PycharmProjects\pycharmpdfhelp\PycharmHelpPDFWithToC.png "Screen capture of PDF")

## Project Notes
At one time, JetBrains was supplying a PDF but they moved to a plugin that downloads the 
web content which then gets served up by their internal server.

PDF documentation is my preference:
- One file portability
- Naturally easy to take offline
- Universal reader access availability
- Easily indexed and searched, and
- Easy to put on an e-Reader or mobile device.

I think there are only two Windows path dependencies need to be changed to use on a non-Windows O/S: 
- Download path [see \_\_init__()]
- Chrome driver path [see setup_selenium_chrome()]

Other notes:
- You can adjust the scaling factor [see "scaling" in setup_selenium_chrome()]
- The program is written so that if you start, stop and restart during the download 
process, it will pick up generation where it was stopped
- There's a slight delay to give the browser time to properly render the page and 
then generate the PDF.
- There's a function that verifies the PDF file sizes "look" correct.
If any are too small, those pages are re-requested and generated again before
master PDF generation.

## TODO
- Fixup internal links to point to PDF pages instead of the web site. 
I may or may not get around to this. My main needs and purpose are met
by the current program. If you are interested in resolving this a pull
request would be most welcome.

