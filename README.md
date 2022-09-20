<ins>Description</ins>

Scrapes student and assignment data from the Canvas LMS at Virginia Tech (and maybe others...)

<ins>Installation</ins>

In the same folder as the _scrape.py_ script, place the Selenium Chrome driver that matches your operating system and version of Google Chrome (https://chromedriver.chromium.org/downloads). For your convenience, the v105 Win32 _chromedrive.exe_ is included in this repository.

<ins>Running</ins>

_python scraper.py [-h] username password course_url_
  - _username_ and _password_ are your Canvas credentials
  - _course_url_ is the Canvas course URL, e.g., https://canvas.vt.edu/courses/123456
  
NOTE: This script assumes that you use Duo Mobile or some compatible 2FA authentication method. You will need to authenticate every time this script is executed. The script will prompt you ("Waiting for 2-Factor Authentication...") when the 2FA push has been sent.

<ins>Output</ins>

All output is written to the same folder as the _scrape.py_ script. The output files are:
- students.csv (student course roster, course grade, etc.)
- assignments.csv (list of course assignments, quizzes, projects, etc.)
- student_assignment_activity.csv (a per assignment view of student activity, e.g. submission dates, late submissions, etc.)
