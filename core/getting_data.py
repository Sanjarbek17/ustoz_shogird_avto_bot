def to_json(lst):
    dct = {'needs': lst[0]}
    dct['text'] = lst[1]
    dct['hashtags'] = lst[2].split(' ')
    dct['url'] = lst[3]
    return dct

def to_text(dct):
    text = f"{dct['needs']}\n\n"
    
    text += dct['text'] + '\n\n'
    text += ' '.join(dct['hashtags']) + '\n'
    text += dct['url']
    return text
        
        