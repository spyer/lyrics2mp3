# lyrics2mp3 
python 3

Parse lyrics and add them into mp3 files (via id tags).  
Lyrics can then be viewed on iPhone, iTunes and other players.  

What script does:  
1. Scans recursively directory for mp3 files.  
2. Reads Artist and title from mp3 tag.  
3. Searches lyrics for each song on azlyrics.com  
4. Inserts lyrics into mp3 file, or '...' if not found (needed not to skip files)  

Installation:  

```
pip install -r requirements.txt
git clone https://github.com/spyer/lyrics2mp3.git
```

If you have trouble installing, please check if **taglib** library is installed (may have to compile). 

Usage:  

```
Required arguments:  
  --dir DIR          Directory to search for mp3 files

```
