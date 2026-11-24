import re
from typing import Dict, List, Optional

# Comprehensive conversational Hinglish dictionary
HINGLISH_DICTIONARY = {
    # Pronouns & People
    'मैं': 'main', 'मै': 'main', 'हूँ': 'hoon', 'हूं': 'hoon', 'हम': 'hum', 'तुम': 'tum',
    'तुम्हें': 'tumhein', 'तुम्हे': 'tumhein', 'तुम्हारा': 'tumhara', 'तुम्हारी': 'tumhari',
    'आप': 'aap', 'आपका': 'aapka', 'आपकी': 'aapki', 'आपके': 'aapke',
    'यह': 'ye', 'ये': 'ye', 'वह': 'woh', 'वो': 'woh', 'इन': 'in', 'उन': 'un',
    'इस': 'is', 'उस': 'us', 'इसे': 'ise', 'उसे': 'use', 'इन्हें': 'inhein', 'उन्हें': 'unhein',
    'भाई': 'bhai', 'यार': 'yaar', 'दोस्त': 'dost', 'बंदा': 'banda', 'बंदे': 'bande',
    'बंदी': 'bandi', 'लोग': 'log', 'लोगों': 'logon', 'सब': 'sab', 'सबको': 'sabko',

    # Common Verbs & Actions
    'है': 'hai', 'हैं': 'hain', 'हो': 'ho', 'था': 'tha', 'थी': 'thi', 'थे': 'the',
    'कर': 'kar', 'करो': 'karo', 'करना': 'karna', 'करते': 'karte', 'करता': 'karta',
    'करती': 'karti', 'किया': 'kiya', 'किए': 'kiye', 'रहा': 'raha', 'रही': 'rahi',
    'रहे': 'rahe', 'दे': 'de', 'दो': 'do', 'देना': 'dena', 'दिया': 'diya', 'दिए': 'diye',
    'ले': 'le', 'लो': 'lo', 'लेना': 'lena', 'लिया': 'liya', 'लिए': 'liye',
    'आ': 'aa', 'आओ': 'aao', 'आना': 'aana', 'आया': 'aaya', 'आई': 'aayi', 'आए': 'aaye',
    'जा': 'ja', 'जाओ': 'jao', 'जाना': 'jaana', 'गया': 'gaya', 'गई': 'gayi', 'गए': 'gaye',
    'देख': 'dekh', 'देखो': 'dekho', 'देखना': 'dekhna', 'देखा': 'dekha', 'देखी': 'dekhi',
    'बोल': 'bol', 'बोलो': 'bolo', 'बोलना': 'bolna', 'बोला': 'bola', 'बोली': 'boli',
    'सुन': 'sun', 'सुनो': 'suno', 'सुनना': 'sunna', 'सुना': 'suna',
    'खेल': 'khel', 'खेलो': 'khelo', 'खेलना': 'khelna', 'खेला': 'khela', 'खेलेंगे': 'khelenge',
    'सकता': 'sakta', 'सकती': 'sakti', 'सकते': 'sakte', 'सकूँ': 'sakoon',
    'रखा': 'rakha', 'रखी': 'rakhi', 'रखे': 'rakhe', 'हुआ': 'hua', 'हुई': 'hui', 'हुए': 'hue',
    'चल': 'chal', 'चलो': 'chalo', 'चला': 'chala', 'चलाई': 'chalayi', 'चलाते': 'chalate',

    # Prepositions & Connectors
    'का': 'ka', 'की': 'ki', 'के': 'ke', 'को': 'ko', 'से': 'se', 'में': 'mein',
    'पे': 'pe', 'पर': 'par', 'ने': 'ne', 'तक': 'tak', 'और': 'aur', 'या': 'ya',
    'तो': 'toh', 'भी': 'bhi', 'ही': 'hi', 'लेकिन': 'lekin', 'मगर': 'magar',
    'क्योंकि': 'kyunki', 'इसलिए': 'isliye', 'अगर': 'agar', 'जब': 'jab', 'तब': 'tab',

    # Questions & Adverbs
    'क्या': 'kya', 'क्यों': 'kyun', 'कहाँ': 'kahan', 'कहा': 'kaha', 'कब': 'kab',
    'कैसे': 'kaise', 'कितना': 'kitna', 'कितनी': 'kitni', 'कितने': 'kitne',
    'नहीं': 'nahi', 'ना': 'na', 'हाँ': 'haan', 'हा': 'haan', 'बस': 'bas',
    'बहुत': 'bahut', 'ज्यादा': 'zyada', 'कम': 'kam', 'थोड़ा': 'thoda', 'थोड़ी': 'thodi',
    'अच्छा': 'achha', 'अच्छी': 'achhi', 'अच्छे': 'achhe', 'बुरा': 'bura',
    'सही': 'sahi', 'गलत': 'galat', 'सच': 'sach', 'झूठ': 'jhooth',

    # Spoken Slang, Reactions & Gaming Terms
    'जीटी': 'GT', 'लास्ट': 'last', 'पंच': 'punch', 'पसंद': 'pasand', 'गेम': 'game',
    'प्ले': 'play', 'क्रेजी': 'crazy', 'लिटरली': 'literally', 'रियल': 'real',
    'कतई': 'katai', 'दिमाग': 'dimag', 'फट': 'phat', 'गसबम्स': 'goosebumps',
    'गूसबम्प्स': 'goosebumps', 'शॉट': 'shot', 'गन': 'gun', 'शॉटगन': 'shotgun',
    'पसीना': 'pasina', 'बाल': 'baal', 'पॉज़': 'pause', 'समझ': 'samajh',
    'रॉकस्टार': 'Rockstar', 'साल': 'saal', 'सालों': 'saalon', 'घंटों': 'ghanton',
    'इंतजार': 'intezaar', 'इंतज़ार': 'intezaar', 'फर्क': 'fark', 'नीचे': 'neeche',
    'ऊपर': 'upar', 'अंदर': 'andar', 'बाहर': 'bahar', 'सामने': 'saamne', 'पीछे': 'peeche',
    'गाड़ी': 'gaadi', 'गाड़ी': 'gaadi', 'कार': 'car', 'बाइक': 'bike', 'स्कूटी': 'scooty',
    'हेडशॉट': 'headshot', 'छक': 'chhak', 'बूम': 'boom', 'इनसेन': 'insane', 'सैवेज': 'savage',
    'डिटेलिंग': 'detailing', 'ग्राफिक्स': 'graphics', 'मैप': 'map', 'इट्स': 'its',
    'फाइनली': 'finally', 'हियर': 'here', 'शकल': 'shakal', 'चेहरा': 'chehra',
    'अरे': 'arre', 'ओ': 'oh', 'हो': 'ho', 'यो': 'yo', 'हंसी': 'hansi', 'संगीत': 'music',
    'रिएक्शन': 'reaction', 'बजट': 'budget', 'करोड़': 'crore', 'करोड़': 'crore',
    'लाख': 'lakh', 'हजार': 'hazaar', 'दिखाओ': 'dikhao', 'दिखा': 'dikha',
    'दिख': 'dikh', 'दिखता': 'dikhta', 'दिखती': 'dikhti', 'दिखते': 'dikhte'
}

VOWELS = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo',
    'ऋ': 'ri', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au', 'अं': 'an', 'अः': 'ah'
}

MATRAS = {
    'ा': 'a', 'ि': 'i', 'ी': 'i', 'ु': 'u', 'ू': 'oo',
    'ृ': 'ri', 'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
    'ं': 'n', 'ँ': 'n', 'ः': 'h', '्': ''
}

CONSONANTS = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v',
    'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
    'क्ष': 'ksh', 'त्र': 'tr', 'ज्ञ': 'gy',
    'क़': 'q', 'ख़': 'kh', 'ग़': 'gh', 'ज़': 'z', 'ड़': 'd', 'ढ़': 'dh', 'फ़': 'f'
}

def transliterate_word(word: str) -> str:
    """Converts a single word to Roman Hinglish using dictionary first, then phonetics."""
    if not word:
        return ""

    # Preserve punctuation
    clean_w = re.sub(r'[\.,\?!;:।\"\'\(\)\[\]]', '', word)
    prefix_punct = ""
    suffix_punct = ""
    m_pref = re.match(r'^[^\w\u0900-\u097F]+', word)
    if m_pref:
        prefix_punct = m_pref.group(0)
    m_suff = re.search(r'[^\w\u0900-\u097F]+$', word)
    if m_suff:
        suffix_punct = m_suff.group(0).replace('।', '.')

    # English word check (if purely Latin characters/numbers)
    if not any('\u0900' <= c <= '\u097F' for c in clean_w):
        return word.replace('।', '.')

    # Exact dictionary lookup (case-insensitive key)
    clean_lower = clean_w.lower()
    for k, v in HINGLISH_DICTIONARY.items():
        if k == clean_w:
            # Capitalize if original was start of sentence
            out_val = v
            if word and word[0].isupper():
                out_val = out_val.capitalize()
            return prefix_punct + out_val + suffix_punct

    # Phonetic transliteration with Hindi schwa deletion
    chars = list(clean_w)
    res = []
    i = 0
    n = len(chars)
    while i < n:
        c = chars[i]
        if c in VOWELS:
            res.append(VOWELS[c])
            i += 1
        elif c in CONSONANTS:
            snd = CONSONANTS[c]
            if i + 1 < n and chars[i+1] == '्':  # Halant
                res.append(snd)
                i += 2
            elif i + 1 < n and chars[i+1] in MATRAS:
                res.append(snd + MATRAS[chars[i+1]])
                i += 2
            else:
                # Schwa deletion rule: Drop trailing 'a' at end of word
                if i == n - 1:
                    res.append(snd)
                else:
                    res.append(snd + 'a')
                i += 1
        elif c in MATRAS:
            res.append(MATRAS[c])
            i += 1
        else:
            # If unknown Devanagari character, skip
            if not ('\u0900' <= c <= '\u097F'):
                res.append(c)
            i += 1

    translit = "".join(res)
    # Quick cleanup
    translit = re.sub(r'ee$', 'i', translit)
    translit = re.sub(r'aa$', 'a', translit)
    return prefix_punct + translit + suffix_punct

def to_hinglish(text: str) -> str:
    """Transliterates any Hindi / Hinglish text to Roman script."""
    if not text:
        return ""
    text = text.replace('।', '.')
    tokens = text.split()
    converted_tokens = [transliterate_word(t) for t in tokens]
    result = " ".join(converted_tokens)
    # Clean double spaces
    result = re.sub(r'\s+', ' ', result).strip()
    return result

def contains_devanagari(text: str) -> bool:
    """Checks if any Devanagari characters remain in text."""
    return any('\u0900' <= c <= '\u097F' for c in text)

