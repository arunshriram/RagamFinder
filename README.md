# RagamFinder
RagamFinder is a prototype tool to identify the possible ragams, or South Indian classical music (Carnatic)  
scales, present in a given file. RagamFinder utilizes FFTs to extract frequencies from the given audio file,  
determines the fundamental frequencies that are present, performs "cleanup" operations on the list of  
fundamental frequencies, and extracts the Carnatic notes given a known tonic pitch. From these extracted notes,  
it then cross-references these notes with a given list of ragams (found in reference/ragam_list.txt) to identify  
the possible ragams. 

## How to run the program
RagamFinder is currently written in Python 3, and uses the following libraries:

 - NumPy  
 - Matplotlib  
 - aubio  
 - PeakUtils  

You can install each of these libraries using the command  
```bash
pip3 install *library_name*  
```
## Usage
The program takes two arguments: the path to the audio file, and a pitch repreenting the sruthi (without pitch  
class). Here is the example I used to obtain the results found in my Senior Project report:  
```bash
python3 RagamFinder.py Arun-voice-testing/maya_full.mp3 C  
```   
As far as I can tell, most audio filetypes should work. I have specifically tested on MP3, WAV, and M4A without  
any troubles.  

## Other help  
For any other questions or concerns regarding running the program, or regarding collaborating on this project,  
please send me an email at arun.shriram@gmail.com, and I will get back to you! 