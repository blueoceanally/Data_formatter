# Data_formatter

Live run: https://huggingface.co/spaces/blueoceanally/data_formatter -->App

1. Add your OpenAI API Key, hit enter
2. choose your template file from local
3. choose your data file from local
4. Click "Reformat" button
5. If mapping is wrong, an error will occur under "Run code", then based on the error, user can manually change the code and fix the mapping.

 
Demo1: Generate mapping.
https://www.youtube.com/watch?v=4tO3EnEWVNc

Demo2: Reuse saved mapping. If a template file and data file name has been processed before, the map code are saved in folder saved/, next time even there are more data in the same file, the system will automatically read from saved mapping code and generate the mapping, unless the file names are unseen before.
https://www.youtube.com/watch?v=Y4imFlNdpRs

Demo3: For ambigious columns, user can choose the column they want to map to.
https://www.youtube.com/watch?v=r1piySXtdUI

Area for improvement:
1. "Generate map code" accuracy can be improved, by fine tune chatgpt's prompt
2. column mapping accuracy can be improved, by either fine tune chatgpt's prompt, or add more manual defined rules
