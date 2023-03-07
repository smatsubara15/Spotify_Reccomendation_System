import pandas as pd
from langdetect import detect
from langdetect import detect_langs

def get_eng_flag(data):
    titles = list(data['track_name'])
    eng_flag = []

    counter = 0 
    for title in titles:
        counter+=1
        print(counter)
        try:
            lang = detect(title)
        except:
            eng_flag.append(0)
        else:
            if(lang=='en'):
                eng_flag.append(1)
            else:
                eng_flag.append(0)
        print(lang)
    print(eng_flag)
    print(len(data))

    data['eng_flag']=eng_flag

data = pd.read_csv("spotify_no_children.csv")
data_new = get_eng_flag(data)
data_new.to_csv('spotify_no_children_w_langflag.csv',mode='w+')

# langdetect works decently, but some non english songs still slip through
            
