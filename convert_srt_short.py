def srt_to_short(srt_string):
     output_list = []

     lines = [line.strip() for line in srt_string.strip().split('\n') if line.strip()]

     i = 0
     while i < len(lines):
          i += 1 #skip seqeuence number

          #get timestamps
          timestamp_line = lines[i]
          start_time, end_time = timestamp_line.split('-->')
          i+= 1

          #get all subtitle text until next seq number
          subtitle_text = []
          while i < len(lines) and not lines[i].isdigit():
               subtitle_text.append(lines[i])
               i+= 1

          #join text lines and format the output
          full_text = ''.join(subtitle_text)
          output_list.append(f"{start_time}, {end_time}, {full_text}")

     return output_list

