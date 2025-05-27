# Templates for Waray language learning app
module_1 = {
    # Module 1: Greetings
    "Lesson 1": [
    {
        "id": 1,
        "type": "Lesson",
        "question": "'Maupay nga aga' means 'Good morning' — maupay is 'good', nga serves as a linker word, and aga means 'morning.'",
        "audio_file": "maupay_nga_aga.mp3",
        "image": "maupay_nga_aga.jpg",
        "answer": None,
        "vocabulary": "Maupay nga aga",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 2,
        "type": "Image Picker",
        "question": "aga",
        "choices": ["morning_sun.jpg", "afternoon_sun.jpg", "night_sky.jpg"],
        "correct_answer": "morning_sun.jpg",
        "vocabulary": "Maupay nga aga",
        "difficulty": 1,
        "response_time": 0
    },
    {
        "id": 3,
        "type": "Translate Sentence",
        "question": "How do you say 'Good morning, Mulay!' in Waray?",
        "choices": ["Maupay nga kulop, Mulay!", "Maupay nga aga, Mulay!"],
        "correct_answer": "Maupay nga aga, Mulay!",
        "vocabulary": "Maupay nga aga",
        "difficulty": 1,
        "response_time": 0
    },
    {
        "id": 4,
        "type": "Pronunciation",
        "question": "How do you pronounce 'aga'?",
        "audio_file": "Maupay nga aga.mp3",
        "accuracy": None,
        "accuracy_threshold": 0.8,
        "vocabulary": "Maupay nga aga",
        "difficulty": 1,
        "response_time": None
    },
    {
        "id": 5,
        "type": "Translate Sentence",
        "question": "You walk into a store at 8 AM. What should you say?",
        "choices": ["Maupay nga aga", "Maupay nga gab-i"],
        "correct_answer": "Maupay nga aga",
        "vocabulary": "Maupay nga aga",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 6,
        "type": "Translate Sentence",
        "question": "Which of these greetings is for the morning?",
        "choices": ["Maupay nga umaga!", "Maupay nga aga!"],
        "correct_answer": "Maupay nga aga!",
        "vocabulary": "Maupay nga aga",
        "difficulty": 2,
        "response_time": 0
    },
    # gihapon section
    {
        "id": 7,
        "type": "Lesson",
        "question": "'Gihapon' means 'too' or 'also' and is used the same way as 'din' in Filipino.",
        "audio_file": "gihapon.mp3",
        "image": "gihapon.jpg",
        "answer": None,
        "vocabulary": "gihapon",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 8,
        "type": "Word Select",
        "question": "Translate to English",
        "word_to_translate": "gihapon",
        "choices": ["too", "maybe", "later"],
        "correct_answer": "too",
        "vocabulary": "gihapon",
        "difficulty": 1,
        "response_time": 0
    },
    {
        "id": 9,
        "type": "True or False",
        "question": "gihapon = also",
        "choices": ["True", "False"],
        "correct_answer": "True",
        "vocabulary": "gihapon",
        "difficulty": 1,
        "response_time": None
    },
    {
        "id": 10,
        "type": "Translate Sentence",
        "question": "How would you say, 'Good morning too!' in Waray?",
        "choices": ["Maupay nga aga rin!", "Maupay nga aga gihapon!"],
        "correct_answer": "Maupay nga aga gihapon!",
        "vocabulary": "gihapon",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 11,
        "type": "Translate Sentence",
        "question": "What does 'Ikaw gihapon' mean?",
        "choices": ["You're new.", "You too."],
        "correct_answer": "You too.",
        "vocabulary": "gihapon",
        "difficulty": 3,
        "response_time": 0
    },
    # kamusta ka section
    {
        "id": 12,
        "type": "Lesson",
        "question": "Kamusta ka? means 'How are you?' in English, and it is exactly the same as in Filipino.",
        "audio_file": "kamusta_ka.mp3",
        "image": "kamusta_ka.jpg",
        "answer": None,
        "vocabulary": "kamusta ka",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 13,
        "type": "True or False",
        "question": "'Kamusta ka?' is the same in both Waray and Filipino.",
        "choices": ["True", "False"],
        "correct_answer": "True",
        "vocabulary": "kamusta ka",
        "difficulty": 1,
        "response_time": None
    },
    {
        "id": 14,
        "type": "True or False",
        "question": "Waray's 'Kamusta ka?' is borrowed from the Filipino language.",
        "choices": ["True", "False"],
        "correct_answer": "True",
        "vocabulary": "kamusta ka",
        "difficulty": 2,
        "response_time": None
    },
    {
        "id": 15,
        "type": "Translate Sentence",
        "question": "How would you greet and ask Raya how she is?",
        "choices": ["Maupay nga aga, Raya. Kamusta ka?", "Maupay nga aga, Raya. Kamusta hiya?"],
        "correct_answer": "Maupay nga aga, Raya. Kamusta ka?",
        "vocabulary": "kamusta ka",
        "difficulty": 3,
        "response_time": 0
    },
    {
        "id": 16,
        "type": "Translate Sentence",
        "question": "How would you respond if someone asks 'Kamusta ka?' and you feel good?",
        "choices": ["Maupay.", "Gihapon."],
        "correct_answer": "Maupay.",
        "vocabulary": "kamusta ka",
        "difficulty": 4,
        "response_time": 0
    },
    # ikaw section
    {
        "id": 17,
        "type": "Lesson",
        "question": "Ikaw? means 'How about you?' in English, the same as in Filipino. It's used to ask about someone else after sharing your own situation.",
        "audio_file": "ikaw.mp3",
        "image": "ikaw.jpg",
        "answer": None,
        "vocabulary": "ikaw?",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 18,
        "type": "True or False",
        "question": "'Ikaw?' in Waray is the same as 'Ikaw?' in Filipino.",
        "choices": ["True", "False"],
        "correct_answer": "True",
        "vocabulary": "ikaw?",
        "difficulty": 1,
        "response_time": None
    },
    {
        "id": 19,
        "type": "Translate Sentence",
        "question": "What does 'Ikaw?' mean?",
        "choices": ["How are you?", "How about you?"],
        "correct_answer": "How about you?",
        "vocabulary": "ikaw?",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 20,
        "type": "Translate Sentence",
        "question": "Jinora: Kamusta ka?\nTara: __________\nHow would you say 'Good. How about you?'?",
        "choices": ["Maupay. Ikaw?", "Gihapon. Ikaw?"],
        "correct_answer": "Maupay. Ikaw?",
        "vocabulary": "ikaw?",
        "difficulty": 3,
        "response_time": 0
    },
    ],
    "Lesson 2": [
    # la section
    {
        "id": 21,
        "type": "Lesson",
        "question": "'Okay la ako' means 'I`m just okay'. 'La' is the Waray word for 'just' or 'only,' same as 'lang' in Filipino.",
        "audio_file": "okay_la_ako.mp3",
        "image": "okay_la_ako.jpg",
        "answer": None,
        "vocabulary": "okay la ako",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 22,
        "type": "Word Select",
        "question": "Translate to English",
        "word_to_translate": "la",
        "choices": ["not", "too", "only"],
        "correct_answer": "only",
        "vocabulary": "okay la ako",
        "difficulty": 1,
        "response_time": 0
    },
    {
        "id": 23,
        "type": "Translate Sentence",
        "question": "When would you use 'Okay la ako' in a conversation?",
        "choices": ["When someone asks 'Kamusta ka?'", "When someone greets you 'Maupay nga aga!'"],
        "correct_answer": "When someone asks 'Kamusta ka?'",
        "vocabulary": "okay la ako",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 24,
        "type": "Translate Sentence",
        "question": "Mari: Kamusta ka?\nHow would you respond to Mari in Waray if you want to say you're just doing okay?",
        "choices": ["Okay la ako.", "Sige la."],
        "correct_answer": "Okay la ako.",
        "vocabulary": "okay la ako",
        "difficulty": 3,
        "response_time": 0
    },
    
    # kulop section
    {
        "id": 25,
        "type": "Lesson",
        "question": "'Maupay nga kulop' means 'Good afternoon.' 'Maupay' means 'good,' and 'kulop' means 'afternoon.'",
        "audio_file": "maupay_nga_kulop.mp3",
        "image": "maupay_nga_kulop.jpg",
        "answer": None,
        "vocabulary": "kulop",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 26,
        "type": "Image Picker",
        "question": "kulop",
        "choices": ["morning_sun.jpg", "afternoon_sun.jpg", "night_sky.jpg"],
        "correct_answer": "afternoon_sun.jpg",
        "vocabulary": "kulop",
        "difficulty": 1,
        "response_time": 0
    },
    {
        "id": 27,
        "type": "Pronunciation",
        "question": "How do you pronounce 'maupay'?",
        "audio_file": "maupay.mp3",
        "accuracy": None,
        "accuracy_threshold": 0.8,
        "vocabulary": "maupay",
        "difficulty": 2,
        "response_time": None
    },
    {
        "id": 28,
        "type": "Translate Sentence",
        "question": "What would you say to greet your friend, Sabel, at 3 PM?",
        "choices": ["Maupay nga aga, Sabel!", "Maupay nga kulop, Sabel!"],
        "correct_answer": "Maupay nga kulop, Sabel!",
        "vocabulary": "kulop",
        "difficulty": 3,
        "response_time": 0
    },
    {
        "id": 29,
        "type": "Translate Sentence",
        "question": "Your friend greets you 'Maupay nga kulop!' What time of day is it?",
        "choices": ["Morning", "Afternoon"],
        "correct_answer": "Afternoon",
        "vocabulary": "kulop",
        "difficulty": 3,
        "response_time": 0
    },
    
    # diri section
    {
        "id": 30,
        "type": "Lesson",
        "question": "'Diri' means 'no' or 'not', while 'Oo' means 'yes'.",
        "audio_file": "diri_oo.mp3",
        "image": "diri_oo.jpg",
        "answer": None,
        "vocabulary": "diri",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 31,
        "type": "Word Select",
        "question": "Translate to Waray",
        "word_to_translate": "No",
        "choices": ["kulop", "oo", "diri"],
        "correct_answer": "diri",
        "vocabulary": "diri",
        "difficulty": 1,
        "response_time": 0
    },
    {
        "id": 32,
        "type": "Translate Sentence",
        "question": "Which of these shows someone saying 'no' in Waray?",
        "choices": ["Oo, maupay!", "Diri ako."],
        "correct_answer": "Diri ako.",
        "vocabulary": "diri",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 33,
        "type": "Translate Sentence",
        "question": "You're invited to join a game and want to say no. What should you say?",
        "choices": ["Oo", "Diri"],
        "correct_answer": "Diri",
        "vocabulary": "diri",
        "difficulty": 3,
        "response_time": 0
    },
    {
        "id": 34,
        "type": "Translate Sentence",
        "question": "Amara: Kamusta ka?\nHow would you respond with 'Not good'?",
        "choices": ["Diri maupay", "Maupay la"],
        "correct_answer": "Diri maupay",
        "vocabulary": "diri",
        "difficulty": 4,
        "response_time": 0
    },
    
    # it section
    {
        "id": 35,
        "type": "Lesson",
        "question": "'It' in Waray is used like 'the' in English and 'ang' in Filipino to refer to something specific.",
        "audio_file": "it.mp3",
        "image": "it.jpg",
        "answer": None,
        "vocabulary": "It",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 36,
        "type": "Word Select",
        "question": "Translate to English",
        "word_to_translate": "It",
        "choices": ["And", "The", "Of"],
        "correct_answer": "The",
        "vocabulary": "It",
        "difficulty": 1,
        "response_time": 0
    },
    {
        "id": 37,
        "type": "Word Select",
        "question": "Translate to Waray",
        "word_to_translate": "the adobo",
        "choices": ["nga sinigang", "ang adobo", "it adobo"],
        "correct_answer": "it adobo",
        "vocabulary": "It",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 38,
        "type": "Translate Sentence",
        "question": "How would you Kayla say 'The Banig'?",
        "choices": ["It banig", "Ang banig"],
        "correct_answer": "It banig",
        "vocabulary": "It",
        "difficulty": 3,
        "response_time": 0
    },
    {
        "id": 39,
        "type": "Translate Sentence",
        "question": "How would you say 'The weather (panahon) is not good'?",
        "choices": ["Diri maupay it panahon.", "Diri maupay ang panahon."],
        "correct_answer": "Diri maupay it panahon.",
        "vocabulary": "It",
        "difficulty": 4,
        "response_time": 0
    },
    ],
    "Lesson 3": [
    # gab-i section
    {
        "id": 40,
        "type": "Lesson",
        "question": "Gab-i means night and is pronounced as 'gab-EE,' with emphasis on the I.",
        "audio_file": "gab-i.mp3",
        "image": "gab-i.jpg",
        "answer": None,
        "vocabulary": "gab-i",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 41,
        "type": "Pronunciation",
        "question": "How do you pronounce 'gab-i'?",
        "audio_file": "gab-i.mp3",
        "accuracy": None,
        "accuracy_threshold": 0.8,
        "vocabulary": "gab-i",
        "difficulty": 1,
        "response_time": None
    },
    {
        "id": 42,
        "type": "Image Picker",
        "question": "gab-i",
        "choices": ["morning_sun.jpg", "afternoon_sun.jpg", "night_sky.jpg"],
        "correct_answer": "night_sky.jpg",
        "vocabulary": "gab-i",
        "difficulty": 1,
        "response_time": 0
    },
    {
        "id": 43,
        "type": "True or False",
        "question": "'Maupay nga gab-i' is used to greet someone in the morning.",
        "choices": ["True", "False"],
        "correct_answer": "False",
        "vocabulary": "gab-i",
        "difficulty": 2,
        "response_time": None
    },
    {
        "id": 44,
        "type": "Translate Sentence",
        "question": "How would you greet others if it's 7 PM?",
        "choices": ["Maupay nga gab-i!", "Maupay nga aga!"],
        "correct_answer": "Maupay nga gab-i!",
        "vocabulary": "gab-i",
        "difficulty": 3,
        "response_time": 0
    },
    {
        "id": 45,
        "type": "Translate Sentence",
        "question": "Emilio: Good evening!\nHow would you greet Emilio back?",
        "choices": ["Maupay nga kulop gihapon!", "Maupay nga gab-i gihapon!"],
        "correct_answer": "Maupay nga gab-i gihapon!",
        "vocabulary": "gab-i",
        "difficulty": 4,
        "response_time": 0
    },
    
    # ano it imo ngaran? section
    {
        "id": 46,
        "type": "Lesson",
        "question": "Ano it imo ngaran? means 'What is your name?' in English. 'Imo' means your, and 'ngaran' means name.",
        "audio_file": "ano_it_imo_ngaran.mp3",
        "image": "ano_it_imo_ngaran.jpg",
        "answer": None,
        "vocabulary": "ano it imo ngaran?",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 47,
        "type": "Pronunciation",
        "question": "How do you pronounce 'ngaran'?",
        "audio_file": "ngaran.mp3",
        "accuracy": None,
        "accuracy_threshold": 0.8,
        "vocabulary": "ngaran",
        "difficulty": 1,
        "response_time": None
    },
    {
        "id": 48,
        "type": "Word Select",
        "question": "Translate to English",
        "word_to_translate": "Name",
        "choices": ["imo", "gihap", "ngaran"],
        "correct_answer": "ngaran",
        "vocabulary": "ngaran",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 49,
        "type": "Translate Sentence",
        "question": "Which one means 'What is your name?'",
        "choices": ["Ano it imo ngaran?", "Maupay it imo ngaran?"],
        "correct_answer": "Ano it imo ngaran?",
        "vocabulary": "ano it imo ngaran?",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 50,
        "type": "Translate Sentence",
        "question": "You want to know your classmate's name. What should you ask?",
        "choices": ["Ano it imo ngaran?", "Kamusta ka?"],
        "correct_answer": "Ano it imo ngaran?",
        "vocabulary": "ano it imo ngaran?",
        "difficulty": 3,
        "response_time": 0
    },
    {
        "id": 51,
        "type": "Translate Sentence",
        "question": "Angelo: Ano it imo ngaran?\nWhat is Angelo asking you?",
        "choices": ["Your age", "Your name"],
        "correct_answer": "Your name",
        "vocabulary": "ano it imo ngaran?",
        "difficulty": 3,
        "response_time": 0
    },
    {
        "id": 52,
        "type": "Translate Sentence",
        "question": "Tara wants to ask Emilio his name after saying good evening.",
        "choices": ["Maupay nga gab-i! Ano it imo ngaran?", "Maupay nga aga! Hain ka?"],
        "correct_answer": "Maupay nga gab-i! Ano it imo ngaran?",
        "vocabulary": "ano it imo ngaran?",
        "difficulty": 4,
        "response_time": 0
    },
    
    # ako hi section
    {
        "id": 53,
        "type": "Lesson",
        "question": "Ako hi (name) means 'I am (name)' in English. 'Hi' is like 'si' in Filipino and is pronounced 'hee.'",
        "audio_file": "ako_hi.mp3",
        "image": "ako_hi.jpg",
        "answer": None,
        "vocabulary": "ako hi",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 54,
        "type": "True or False",
        "question": "'Ako hi.' means 'I am' and is used to introduce yourself.",
        "choices": ["True", "False"],
        "correct_answer": "True",
        "vocabulary": "ako hi",
        "difficulty": 1,
        "response_time": None
    },
    {
        "id": 55,
        "type": "Image Picker",
        "question": "Ako hi Leni.",
        "choices": ["person_pointing_self.jpg", "person_pointing_other.jpg", "person_waving.jpg"],
        "correct_answer": "person_pointing_self.jpg",
        "vocabulary": "ako hi",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 56,
        "type": "Translate Sentence",
        "question": "How would you introduce yourself as Maria?",
        "choices": ["Ako hi Maria.", "It Maria ako."],
        "correct_answer": "Ako hi Maria.",
        "vocabulary": "ako hi",
        "difficulty": 3,
        "response_time": 0
    },
    {
        "id": 57,
        "type": "Translate Sentence",
        "question": "Sol: Ano it imo ngaran?\nWhat is the appropriate response?",
        "choices": ["Maupay it gab-i.", "Ako hi Luna."],
        "correct_answer": "Ako hi Luna.",
        "vocabulary": "ako hi",
        "difficulty": 4,
        "response_time": 0
    },
    {
        "id": 58,
        "type": "Translate Sentence",
        "question": "How would you introduce yourself as Maya and ask the name of the person you're talking to?",
        "choices": ["Ako hi Maya. Ikaw gihapon?", "Ako hi Maya. Ano it imo ngaran?"],
        "correct_answer": "Ako hi Maya. Ano it imo ngaran?",
        "vocabulary": "ako hi",
        "difficulty": 5,
        "response_time": 0
    },
    ],
    "Lesson 4": [
    # damo nga salamat section
    {
        "id": 59,
        "type": "Lesson",
        "question": "Damo nga salamat means 'Thank you very much!' in English. 'Damo' means 'a lot' or 'many', and 'salamat' means 'thanks'.",
        "audio_file": "damo_nga_salamat.mp3",
        "image": "damo_nga_salamat.jpg",
        "answer": None,
        "vocabulary": "damo nga salamat",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 60,
        "type": "Translate Sentence",
        "question": "How would you say 'Thank you very much!'?",
        "choices": ["Damo nga salamat!", "Maupay nga salamat!"],
        "correct_answer": "Damo nga salamat!",
        "vocabulary": "damo nga salamat",
        "difficulty": 1,
        "response_time": 0
    },
    {
        "id": 61,
        "type": "True or False",
        "question": "You say 'Damo nga salamat.' to express your gratitude.",
        "choices": ["True", "False"],
        "correct_answer": "True",
        "vocabulary": "damo nga salamat",
        "difficulty": 2,
        "response_time": None
    },
    {
        "id": 62,
        "type": "Translate Sentence",
        "question": "Nadia cooked a delicious meal for you. How would you thank her in Waray?",
        "choices": ["Maupay nga gab-i, Nadia!", "Damo nga salamat, Nadia!"],
        "correct_answer": "Damo nga salamat, Nadia!",
        "vocabulary": "damo nga salamat",
        "difficulty": 3,
        "response_time": 0
    },
    {
        "id": 63,
        "type": "Word Select",
        "question": "Translate this to English",
        "word_to_translate": "Damo",
        "choices": ["Very", "Many", "Few"],
        "correct_answer": "Many",
        "vocabulary": "damo",
        "difficulty": 4,
        "response_time": 0
    },
    {
        "id": 64,
        "type": "Translate Sentence",
        "question": "Aluna: Maupay nga aga! Kamusta ka?\nHow would you tell Aluna, 'I'm okay. Thanks a lot!'?",
        "choices": ["Okay la ako. Maupay!", "Okay la ako. Damo nga salamat!"],
        "correct_answer": "Okay la ako. Damo nga salamat!",
        "vocabulary": "damo nga salamat",
        "difficulty": 5,
        "response_time": 0
    },
    
    # waray sapayan section
    {
        "id": 65,
        "type": "Lesson",
        "question": "'Waray sapayan!' means 'You're welcome!' or directly 'No matter!' in English",
        "audio_file": "waray_sapayan.mp3",
        "image": "waray_sapayan.jpg",
        "answer": None,
        "vocabulary": "waray sapayan",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 66,
        "type": "Word Select",
        "question": "Translate to English",
        "word_to_translate": "Waray sapayan!",
        "choices": ["You're welcome!", "Thanks a lot!", "Maupay ka!"],
        "correct_answer": "You're welcome!",
        "vocabulary": "waray sapayan",
        "difficulty": 1,
        "response_time": 0
    },
    {
        "id": 67,
        "type": "Word Select",
        "question": "Translate to Waray",
        "word_to_translate": "You're welcome!",
        "choices": ["Waray salamat!", "Waray sapayan!", "Waray ngaran!"],
        "correct_answer": "Waray sapayan!",
        "vocabulary": "waray sapayan",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 68,
        "type": "Translate Sentence",
        "question": "When someone says 'Waray sapayan', they are:",
        "choices": ["Saying you're welcome", "Asking how you are"],
        "correct_answer": "Saying you're welcome",
        "vocabulary": "waray sapayan",
        "difficulty": 3,
        "response_time": 0
    },
    {
        "id": 69,
        "type": "Translate Sentence",
        "question": "John: Damo nga salamat!\nHow would you respond to John's thanks?",
        "choices": ["Waray sapayan.", "Maupay nga aga."],
        "correct_answer": "Waray sapayan.",
        "vocabulary": "waray sapayan",
        "difficulty": 4,
        "response_time": 0
    },
    
    # pasaylo-a ako section (continued)
    {
        "id": 70,
        "type": "Lesson",
        "question": "'Pasaylo-a' ako means 'I'm sorry' or 'Forgive me' in English — 'pasaylo-a' means 'forgive'.",
        "audio_file": "pasaylo-a_ako.mp3",
        "image": "pasaylo-a_ako.jpg",
        "answer": None,
        "vocabulary": "pasaylo-a ako",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 71,
        "type": "Word Select",
        "question": "Translate to English",
        "word_to_translate": "Pasaylo-a ako.",
        "choices": ["I'm sorry.", "Excuse me.", "I'm done."],
        "correct_answer": "I'm sorry.",
        "vocabulary": "pasaylo-a ako",
        "difficulty": 1,
        "response_time": 0
    },
    {
        "id": 72,
        "type": "Translate Sentence",
        "question": "Which phrase would you use to apologize in Waray?",
        "choices": ["Damo nga salamat.", "Pasaylo-a ako."],
        "correct_answer": "Pasaylo-a ako.",
        "vocabulary": "pasaylo-a ako",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 73,
        "type": "Word Select",
        "question": "Translate to Waray",
        "word_to_translate": "I'm sorry.",
        "choices": ["Waray sapayan.", "Pasaylo-a ako.", "Maupay ako."],
        "correct_answer": "Pasaylo-a ako.",
        "vocabulary": "pasaylo-a ako",
        "difficulty": 3,
        "response_time": 0
    },
    {
        "id": 74,
        "type": "Translate Sentence",
        "question": "You accidentally step on someone's foot. How should you apologize?",
        "choices": ["Pasaylo-a ako.", "Maupay nga aga."],
        "correct_answer": "Pasaylo-a ako.",
        "vocabulary": "pasaylo-a ako",
        "difficulty": 4,
        "response_time": 0
    },
    {
        "id": 75,
        "type": "Translate Sentence",
        "question": "Allen: Maupay nga aga!\nAllen realizes it's 3PM already. How would he say 'I'm sorry. Good afternoon.'",
        "choices": ["Pasaylo-a ako. Maupay nga kulop.", "Waray sapayan. Maupay nga kulop."],
        "correct_answer": "Pasaylo-a ako. Maupay nga kulop.",
        "vocabulary": "pasaylo-a ako",
        "difficulty": 5,
        "response_time": 0
    },
    ],
    "Lesson 5": [
    # maaram ka mag-english section
    {
        "id": 76,
        "type": "Lesson",
        "question": "Maaram ka mag-English? means 'Do you know how to speak English?' in English. 'Maaram' means 'to know,' used similar to 'Marunong' in Filipino.",
        "audio_file": "maaram_ka_mag-english.mp3",
        "image": "maaram_ka_mag-english.jpg",
        "answer": None,
        "vocabulary": "maaram ka mag-english",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 77,
        "type": "True or False",
        "question": "'Maaram ka mag-English?' asks if who you're talking to can speak English.",
        "choices": ["True", "False"],
        "correct_answer": "True",
        "vocabulary": "maaram ka mag-english",
        "difficulty": 1,
        "response_time": None
    },
    {
        "id": 78,
        "type": "Translate Sentence",
        "question": "Translate this: 'Do you know how to speak English?'",
        "choices": ["Maaram ka mag-English?", "Kamusta ka mag-English?"],
        "correct_answer": "Maaram ka mag-English?",
        "vocabulary": "maaram ka mag-english",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 79,
        "type": "Word Select",
        "question": "You need help from someone who speaks English. What would you ask?",
        "choices": ["Ano it imo ngaran?", "Maaram ka mag-English?"],
        "correct_answer": "Maaram ka mag-English?",
        "vocabulary": "maaram ka mag-english",
        "difficulty": 3,
        "response_time": 0
    },
    {
        "id": 80,
        "type": "Translate Sentence",
        "question": "You're having difficulty speaking in Waray and you want to switch to English. How do you ask someone if they can speak English?",
        "choices": ["Waray English?", "Maaram ka mag-English?"],
        "correct_answer": "Maaram ka mag-English?",
        "vocabulary": "maaram ka mag-english",
        "difficulty": 4,
        "response_time": 0
    },

    # diri ako makarit ha waray section
    {
        "id": 81,
        "type": "Lesson",
        "question": "Diri ako makarit ha Waray means 'I'm not good at Waray.' Say this when you're struggling to understand Waray or need to explain your limited ability.",
        "audio_file": "diri_ako_makarit_ha_waray.mp3",
        "image": "diri_ako_makarit_ha_waray.jpg",
        "answer": None,
        "vocabulary": "diri ako makarit ha waray",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 82,
        "type": "Translate Sentence",
        "question": "What does 'Diri ako makarit ha Waray' mean?",
        "choices": ["I speak Waray well.", "I don't speak Waray well."],
        "correct_answer": "I don't speak Waray well.",
        "vocabulary": "diri ako makarit ha waray",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 83,
        "type": "Translate Sentence",
        "question": "How would you tell someone you're not good at speaking Waray?",
        "choices": ["Diri ako makarit ha Waray.", "Maaram ako mag-Waray."],
        "correct_answer": "Diri ako makarit ha Waray.",
        "vocabulary": "diri ako makarit ha waray",
        "difficulty": 3,
        "response_time": 0
    },
    {
        "id": 84,
        "type": "Translate Sentence",
        "question": "Someone is speaking Waray to you quickly, and you're having trouble understanding. What should you say?",
        "choices": ["Diri ako makarit ha Waray.", "Maupay nga aga."],
        "correct_answer": "Diri ako makarit ha Waray.",
        "vocabulary": "diri ako makarit ha waray",
        "difficulty": 4,
        "response_time": 0
    },
    {
        "id": 85,
        "type": "Translate Sentence",
        "question": "Andres: Alayon!\nYou don't understand Andres. How would you apologize and say you're not good at Waray?",
        "choices": ["Pasaylo-a ako, diri ako makarit ha Waray.", "Waray sapayan, diri ako makarit ha Waray."],
        "correct_answer": "Pasaylo-a ako, diri ako makarit ha Waray.",
        "vocabulary": "diri ako makarit ha waray",
        "difficulty": 5,
        "response_time": 0
    },

    # ambot section
    {
        "id": 86,
        "type": "Lesson",
        "question": "Ambot means 'I don't know' in Waray, the same as 'ewan' in Filipino. Use it when you're uncertain or don't have an answer.",
        "audio_file": "ambot.mp3",
        "image": "ambot.jpg",
        "answer": None,
        "vocabulary": "ambot",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 87,
        "type": "True or False",
        "question": "'Ambot' means 'I don't know' in Waray.",
        "choices": ["True", "False"],
        "correct_answer": "True",
        "vocabulary": "ambot",
        "difficulty": 1,
        "response_time": None
    },
    {
        "id": 88,
        "type": "Word Select",
        "question": "Translate to English",
        "word_to_translate": "Ambot",
        "choices": ["I guess.", "I know.", "I don't know."],
        "correct_answer": "I don't know.",
        "vocabulary": "ambot",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 89,
        "type": "Image Picker",
        "question": "ambot",
        "choices": ["person_nodding.jpg", "person_shrugging.jpg", "person_smiling.jpg"],
        "correct_answer": "person_shrugging.jpg",
        "vocabulary": "ambot",
        "difficulty": 3,
        "response_time": 0
    },
    {
        "id": 90,
        "type": "Translate Sentence",
        "question": "Someone asks you a question you don't know the answer to. What would you say?",
        "choices": ["Ambot", "Maupay"],
        "correct_answer": "Ambot",
        "vocabulary": "ambot",
        "difficulty": 4,
        "response_time": 0
    }
    ],
}

module_2 = {
    # Module 2: Transportation
    # Lesson 1: Basic Location Questions
    "Lesson 1": [
    {
        "id": 101,
        "type": "Lesson",
        "question": "Hain ka? means 'Where are you?' in English. It's used when asking someone where they are. 'Hain' means 'where.'",
        "audio_file": "hain_ka.mp3",
        "image": "hain_ka.jpg",
        "answer": None,
        "vocabulary": "Hain ka?",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 102,
        "type": "Word Select",
        "question": "Translate to English",
        "word_to_translate": "hain",
        "choices": ["hino", "hain", "kayano"],
        "correct_answer": "hain",
        "vocabulary": "hain",
        "difficulty": 1,
        "response_time": 0
    },
    {
        "id": 103,
        "type": "Pronunciation",
        "question": "How do you pronounce 'hain'?",
        "audio_file": "hain.mp3",
        "accuracy": None,
        "accuracy_threshold": 0.8,
        "vocabulary": "hain",
        "difficulty": 1,
        "response_time": None
    },
    {
        "id": 104,
        "type": "Translate Sentence",
        "question": "Your friend calls you on the phone. How would they ask where you are?",
        "choices": ["Hain ka?", "Kamusta ka?"],
        "correct_answer": "Hain ka?",
        "vocabulary": "Hain ka?",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 105,
        "type": "Lesson",
        "question": "Makain ka? means 'Where are you going?' in English. It's used to ask where someone is headed.",
        "audio_file": "makain_ka.mp3",
        "image": "makain_ka.jpg",
        "answer": None,
        "vocabulary": "Makain ka?",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 106,
        "type": "True or False",
        "question": "'Makain ka?' is used to ask someone where they are headed.",
        "choices": ["True", "False"],
        "correct_answer": "True",
        "vocabulary": "Makain ka?",
        "difficulty": 1,
        "response_time": None
    },
    {
        "id": 107,
        "type": "Translate Sentence",
        "question": "How would you ask your sister where she is going?",
        "choices": ["Makain ka?", "Hain ka?"],
        "correct_answer": "Makain ka?",
        "vocabulary": "Makain ka?",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 108,
        "type": "Translate Sentence",
        "question": "You see your friend with a backpack heading out. How would you ask where they're going?",
        "choices": ["Hain ka?", "Makain ka?"],
        "correct_answer": "Makain ka?",
        "vocabulary": "Makain ka?",
        "difficulty": 3,
        "response_time": 0
    },
    {
        "id": 109,
        "type": "Lesson",
        "question": "Lakat kita means 'Let's go out' or 'Let's hang out' in English. It's used when inviting someone to go or leave together.",
        "audio_file": "lakat_kita.mp3",
        "image": "lakat_kita.jpg",
        "answer": None,
        "vocabulary": "Lakat kita",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 110,
        "type": "True or False",
        "question": "Translate this to Waray: Let's go out!",
        "choices": ["Makain kita!", "Lakat kita!"],
        "correct_answer": "Lakat kita!",
        "vocabulary": "Lakat kita",
        "difficulty": 1,
        "response_time": None
    },
    {
        "id": 111,
        "type": "Image Picker",
        "question": "Lakat kita",
        "choices": ["friends_walking.jpg", "person_sitting.jpg", "person_asking.jpg"],
        "correct_answer": "friends_walking.jpg",
        "vocabulary": "Lakat kita",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 112,
        "type": "Translate Sentence",
        "question": "How would you ask Amira to hang out with you?",
        "choices": ["Makain kita, Amira.", "Lakat kita, Amira."],
        "correct_answer": "Lakat kita, Amira.",
        "vocabulary": "Lakat kita",
        "difficulty": 3,
        "response_time": 0
    },
    ],
    # Lesson 2: Public Transportation
    "Lesson 2": [
    {
        "id": 113,
        "type": "Lesson",
        "question": "Pakadto kita ha (place) means 'Let's go to (place)' in English. It is used to invite someone to go somewhere with you.",
        "audio_file": "pakadto_kita.mp3",
        "image": "pakadto_kita.jpg",
        "answer": None,
        "vocabulary": "Pakadto kita ha",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 114,
        "type": "True or False",
        "question": "Pakadto is the same as 'pumunta' in Filipino.",
        "choices": ["True", "False"],
        "correct_answer": "True",
        "vocabulary": "Pakadto",
        "difficulty": 2,
        "response_time": None
    },
    {
        "id": 115,
        "type": "Translate Sentence",
        "question": "How would you invite your friend to go to the mall with you?",
        "choices": ["Pakadto kita ha mall!", "Hain it mall?"],
        "correct_answer": "Pakadto kita ha mall!",
        "vocabulary": "Pakadto kita ha",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 116,
        "type": "Cultural Trivia",
        "question": "McArthur Park fun fact",
        "choices": ["Option 1", "Option 2"],
        "correct_answer": "Option 1",
        "vocabulary": None,
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 117,
        "type": "Lesson",
        "question": "Para! requests the jeepney driver to stop. The same with Filipino!",
        "audio_file": "para.mp3",
        "image": "para.jpg",
        "answer": None,
        "vocabulary": "Para",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 118,
        "type": "Word Select",
        "question": "How would you ask the jeepney driver to stop?",
        "choices": ["Alayon", "Para"],
        "correct_answer": "Para",
        "vocabulary": "Para",
        "difficulty": 1,
        "response_time": 0
    },
    {
        "id": 119,
        "type": "Lesson",
        "question": "Tagpira it pasahe pa-(place)? means 'How much is the fare to (place)?' in English. You use this when asking how much you need to pay for transportation like jeepney, or tricycle.",
        "audio_file": "tagpira_it_pasahe.mp3",
        "image": "tagpira_it_pasahe.jpg",
        "answer": None,
        "vocabulary": "Tagpira it pasahe",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 120,
        "type": "Word Select",
        "question": "Translate to Waray: How much?",
        "choices": ["Kayano?", "Alayon?", "Tagpira?"],
        "correct_answer": "Tagpira?",
        "vocabulary": "Tagpira",
        "difficulty": 1,
        "response_time": 0
    },
    {
        "id": 121,
        "type": "Translate Sentence",
        "question": "Before boarding a jeepney, how would you ask about the fare?",
        "choices": ["Tagpira it pasahe?", "Para it pasahe?"],
        "correct_answer": "Tagpira it pasahe?",
        "vocabulary": "Tagpira it pasahe",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 122,
        "type": "Translate Sentence",
        "question": "You want to know how much the pedicab ride costs. What do you ask?",
        "choices": ["Pakadto it pasahe?", "Tagpira it pasahe?"],
        "correct_answer": "Tagpira it pasahe?",
        "vocabulary": "Tagpira it pasahe",
        "difficulty": 3,
        "response_time": 0
    },
    ],
    # Lesson 3: Getting Around
    "Lesson 3 ": [
    {
        "id": 123,
        "type": "Lesson",
        "question": "Alayon means 'please' in Waray. On a jeep, you can say 'Alayon pasahe' to politely ask someone to pass your fare.",
        "audio_file": "alayon.mp3",
        "image": "alayon.jpg",
        "answer": None,
        "vocabulary": "Alayon",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 124,
        "type": "Pronunciation",
        "question": "How do you pronounce 'Alayon'?",
        "audio_file": "alayon.mp3",
        "accuracy": None,
        "accuracy_threshold": 0.8,
        "vocabulary": "Alayon",
        "difficulty": 1,
        "response_time": None
    },
    {
        "id": 125,
        "type": "Image Picker",
        "question": "Alayon",
        "choices": ["person_asking_politely.jpg", "person_demanding.jpg", "person_angry.jpg"],
        "correct_answer": "person_asking_politely.jpg",
        "vocabulary": "Alayon",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 126,
        "type": "Word Select",
        "question": "Translate to English: Alayon",
        "choices": ["Please", "Excuse me", "Sorry"],
        "correct_answer": "Please",
        "vocabulary": "Alayon",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 127,
        "type": "Lesson",
        "question": "Hirayo means 'far' in English, describing something at a great distance, similar to 'malayo' in Filipino.",
        "audio_file": "hirayo.mp3",
        "image": "hirayo.jpg",
        "answer": None,
        "vocabulary": "Hirayo",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 128,
        "type": "Word Select",
        "question": "Translate to Waray: far",
        "choices": ["hirani", "hirayo", "haiya"],
        "correct_answer": "hirayo",
        "vocabulary": "Hirayo",
        "difficulty": 1,
        "response_time": 0
    },
    {
        "id": 129,
        "type": "Image Picker",
        "question": "hirayo",
        "choices": ["distant_mountain.jpg", "nearby_house.jpg", "middle_distance.jpg"],
        "correct_answer": "distant_mountain.jpg",
        "vocabulary": "Hirayo",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 130,
        "type": "Lesson",
        "question": "Hirani means 'near' or 'close' in English, describing something nearby, similar to 'malapit' in Filipino.",
        "audio_file": "hirani.mp3",
        "image": "hirani.jpg",
        "answer": None,
        "vocabulary": "Hirani",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 131,
        "type": "Word Select",
        "question": "Translate to Waray: near",
        "choices": ["Haiya", "Hirayo", "Hirani"],
        "correct_answer": "Hirani",
        "vocabulary": "Hirani",
        "difficulty": 1,
        "response_time": 0
    },
    {
        "id": 132,
        "type": "Image Picker",
        "question": "Hirani",
        "choices": ["distant_mountain.jpg", "nearby_house.jpg", "middle_distance.jpg"],
        "correct_answer": "nearby_house.jpg",
        "vocabulary": "Hirani",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 133,
        "type": "True or False",
        "question": "Hirani describes something that is close by or nearby.",
        "choices": ["True", "False"],
        "correct_answer": "True",
        "vocabulary": "Hirani",
        "difficulty": 2,
        "response_time": None
    },
    {
        "id": 134,
        "type": "Translate Sentence",
        "question": "How would you say 'The market (merkado) is near' in Waray?",
        "choices": ["Hirani it merkado.", "Hirayo it merkado."],
        "correct_answer": "Hirani it merkado.",
        "vocabulary": "Hirani",
        "difficulty": 3,
        "response_time": 0
    },
    ],
    # Lesson 4: Direction and Time
    "Lesson 4": [
    {
        "id": 135,
        "type": "Lesson",
        "question": "Aadi means 'here' or 'this way' in English. Use it when pointing to your spot or something nearby, like when riding a jeep.",
        "audio_file": "aadi.mp3",
        "image": "aadi.jpg",
        "answer": None,
        "vocabulary": "Aadi",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 136,
        "type": "Word Select",
        "question": "Translate to Waray: here",
        "choices": ["aadi", "yana", "buwas"],
        "correct_answer": "aadi",
        "vocabulary": "Aadi",
        "difficulty": 1,
        "response_time": 0
    },
    {
        "id": 137,
        "type": "Image Picker",
        "question": "aadi",
        "choices": ["pointing_here.jpg", "pointing_there.jpg", "pointing_nowhere.jpg"],
        "correct_answer": "pointing_here.jpg",
        "vocabulary": "Aadi",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 138,
        "type": "Translate Sentence",
        "question": "Your friend is asking where his keys are. How would you say 'Here'?",
        "choices": ["Waray", "Aadi"],
        "correct_answer": "Aadi",
        "vocabulary": "Aadi",
        "difficulty": 3,
        "response_time": 0
    },
    {
        "id": 139,
        "type": "Lesson",
        "question": "Yana means 'now' or 'today' in English. Use it when talking about current time or asking about present schedules.",
        "audio_file": "yana.mp3",
        "image": "yana.jpg",
        "answer": None,
        "vocabulary": "Yana",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 140,
        "type": "Word Select",
        "question": "Translate to Waray: today",
        "choices": ["niyan", "yana", "buwas"],
        "correct_answer": "yana",
        "vocabulary": "Yana",
        "difficulty": 1,
        "response_time": 0
    },
    {
        "id": 141,
        "type": "Translate Sentence",
        "question": "The jeepney driver asks when you want to leave. How would you say 'today'?",
        "choices": ["Buwas", "Yana"],
        "correct_answer": "Yana",
        "vocabulary": "Yana",
        "difficulty": 1,
        "response_time": 0
    },
    {
        "id": 142,
        "type": "Lesson",
        "question": "Buwas means 'tomorrow' in English. It's the Waray word for 'bukas' in Filipino.",
        "audio_file": "buwas.mp3",
        "image": "buwas.jpg",
        "answer": None,
        "vocabulary": "Buwas",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 143,
        "type": "Word Select",
        "question": "Translate to Waray: tomorrow",
        "choices": ["niyan", "yana", "buwas"],
        "correct_answer": "buwas",
        "vocabulary": "Buwas",
        "difficulty": 1,
        "response_time": 0
    },
    {
        "id": 144,
        "type": "Pronunciation",
        "question": "How do you pronounce 'buwas'?",
        "audio_file": "buwas.mp3",
        "accuracy": None,
        "accuracy_threshold": 0.8,
        "vocabulary": "Buwas",
        "difficulty": 2,
        "response_time": None
    },
    {
        "id": 145,
        "type": "Translate Sentence",
        "question": "How would you invite your friend to go out tomorrow?",
        "choices": ["Lakat kita yana!", "Lakat kita buwas!"],
        "correct_answer": "Lakat kita buwas!",
        "vocabulary": "Buwas",
        "difficulty": 3,
        "response_time": 0
    },
    ],
    # Lesson 5: Additional Travel Phrases
    "Lesson 5": [
    {
        "id": 146,
        "type": "Lesson",
        "question": "San-o? means 'when?' in English.",
        "audio_file": "san-o.mp3",
        "image": "san-o.jpg",
        "answer": None,
        "vocabulary": "San-o?",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 147,
        "type": "True or False",
        "question": "'San-o?' is used to ask about time or schedule.",
        "choices": ["True", "False"],
        "correct_answer": "True",
        "vocabulary": "San-o?",
        "difficulty": 1,
        "response_time": None
    },
    {
        "id": 148,
        "type": "Word Select",
        "question": "Translate to Waray: When?",
        "choices": ["Hain?", "San-o?", "Hino?"],
        "correct_answer": "San-o?",
        "vocabulary": "San-o?",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 149,
        "type": "Translate Sentence",
        "question": "Your friend asks you to dinner. How would you ask when?",
        "choices": ["San-o?", "Kayano?"],
        "correct_answer": "San-o?",
        "vocabulary": "San-o?",
        "difficulty": 3,
        "response_time": 0
    },
    {
        "id": 150,
        "type": "Lesson",
        "question": "Hinay means 'slow' or 'be careful' in English, similar to 'ingat' in Filipino. It is commonly used to tell someone to take care.",
        "audio_file": "hinay.mp3",
        "image": "hinay.jpg",
        "answer": None,
        "vocabulary": "Hinay",
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 151,
        "type": "True or False",
        "question": "'Hinay' can mean both 'slow down' and 'be careful' in Waray.",
        "choices": ["True", "False"],
        "correct_answer": "True",
        "vocabulary": "Hinay",
        "difficulty": 1,
        "response_time": None
    },
    {
        "id": 152,
        "type": "Word Select",
        "question": "Translate to Waray: Take care!",
        "choices": ["Ingat!", "Amping!", "Hinay!"],
        "correct_answer": "Hinay!",
        "vocabulary": "Hinay",
        "difficulty": 2,
        "response_time": 0
    },
    {
        "id": 153,
        "type": "Translate Sentence",
        "question": "How would you tell someone to take care when they are leaving?",
        "choices": ["Hirani!", "Hinay!"],
        "correct_answer": "Hinay!",
        "vocabulary": "Hinay",
        "difficulty": 3,
        "response_time": 0
    }
    ]
}

# Templates for Waray language learning app - Module 3: Shopping and Buying

module_3 = {
    # Module 3: Shopping and Buying
    "Lesson 1": [
    {
        "id": 154, 
        "type": "Lesson", 
        "question": "Maupay means 'good' in Waray, but it's also used to call a vendor in markets, like 'Tao po!' in Filipino.", 
        "audio_file": "maupay.mp3", 
        "image": "maupay_market.jpg", 
        "answer": None, 
        "vocabulary": "Maupay", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 155, 
        "type": "True or False", 
        "question": "'Maupay' can be used to get a vendor's attention in a store.", 
        "choices": ["True", "False"], 
        "correct_answer": "True", 
        "vocabulary": "Maupay", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 156, 
        "type": "Pronunciation", 
        "question": "How do you pronounce 'Maupay'?", 
        "audio_file": "maupay.mp3", 
        "accuracy": None, 
        "accuracy_threshold": 0.8, 
        "vocabulary": "Maupay", 
        "difficulty": 2, 
        "response_time": None
    },
    {
        "id": 157, 
        "type": "Image Picker", 
        "question": "Maupay", 
        "choices": ["vendor_stall.jpg", "night_market.jpg", "closed_store.jpg"], 
        "correct_answer": "vendor_stall.jpg", 
        "vocabulary": "Maupay", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 158, 
        "type": "Lesson", 
        "question": "'Ano ini?' means 'What is this?' in Waray. 'Ini' refers to something close to you.", 
        "audio_file": "ano_ini.mp3", "image": "ano_ini.jpg", 
        "answer": None, 
        "vocabulary": "Ano ini", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 159, 
        "type": "Image Picker", 
        "question": "ini", 
        "choices": ["near_item.jpg", "far_item.jpg", "middle_item.jpg"], 
        "correct_answer": "near_item.jpg", 
        "vocabulary": "ini", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 160, 
        "type": "Word Select", 
        "question": "How would you say 'What is this?' in Waray?", 
        "choices": ["Ano iton?", "Ano ini?"], 
        "correct_answer": "Ano ini?", 
        "vocabulary": "Ano ini", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 161, 
        "type": "Translate Sentence", 
        "question": "Pedro wants to ask what the bag he's holding is. What would he say?", 
        "choices": ["Ano iton?", "Ano ini?"], 
        "correct_answer": "Ano ini?", 
        "vocabulary": "Ano ini", 
        "difficulty": 3, 
        "response_time": 0
    },
    {
        "id": 162,
        "type": "Lesson", 
        "question": "'Ano iton?' means 'What is that?' in Waray. 'Iton' refers to something near the listener.", 
        "audio_file": "ano_iton.mp3", 
        "image": "ano_iton.jpg", 
        "answer": None, 
        "vocabulary": "Ano iton", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 163, 
        "type": "Image Picker", 
        "question": "iton", 
        "choices": ["far_item.jpg", "near_item.jpg", "middle_item.jpg"], 
        "correct_answer": "far_item.jpg", 
        "vocabulary": "iton", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 164, 
        "type": "Word Select", 
        "question": "How would you say 'What is that?' in Waray?", 
        "choices": ["Ano iton?", "Ano ini?"], 
        "correct_answer": "Ano iton?", 
        "vocabulary": "Ano iton", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 165, 
        "type": "Translate Sentence", 
        "question": "Josie is pointing at something her friend is holding. What would she ask?", 
        "choices": ["Ano iton?", "Ano ini?"], 
        "correct_answer": "Ano iton?", 
        "vocabulary": "Ano iton", 
        "difficulty": 3, 
        "response_time": 0
    },
    ],
    "Lesson 2": [
    {
        "id": 166, 
        "type": "Lesson", 
        "question": "'Mapalit ako hin (item)' means 'I want to buy (item).' 'Mapalit' means to buy.", 
        "audio_file": "mapalit_ako.mp3", 
        "image": "mapalit.jpg", 
        "answer": None, 
        "vocabulary": "Mapalit ako hin", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 167, 
        "type": "Word Select", 
        "question": "Which means 'to buy' in Waray?", 
        "choices": ["Maaro", "Mapalit"], 
        "correct_answer": "Mapalit", 
        "vocabulary": "Mapalit", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 168, 
        "type": "Image Picker", 
        "question": "Mapalit ako hin sapatos!", 
        "choices": ["shoes.jpg", "hat.jpg", "shirt.jpg"], 
        "correct_answer": "shoes.jpg", 
        "vocabulary": "Mapalit", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 169, 
        "type": "Translate Sentence", 
        "question": "How would Corazon say she will buy a Tacloban keychain?", 
        "choices": ["Mapalit ako hin keychain.", "Maupay ini nga keychain."], 
        "correct_answer": "Mapalit ako hin keychain.", 
        "vocabulary": "Mapalit", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 170, 
        "type": "Lesson", 
        "question": "'Ngan' means 'and' in English and is used to connect items.", 
        "audio_file": "ngan.mp3", 
        "image": "ngan.jpg", 
        "answer": None, 
        "vocabulary": "ngan", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 171, 
        "type": "Translate Sentence", 
        "question": "How would you say 'and' in Waray?", 
        "choices": ["hin", "ngan"], 
        "correct_answer": "ngan", 
        "vocabulary": "ngan", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 172, 
        "type": "Translate Sentence", 
        "question": "Alaya wants to buy paint and brush. What should she say?", 
        "choices": ["Mapalit ako hin paint ngan brush.", "Mapaalayon hin paint ngan brush."], 
        "correct_answer": "Mapalit ako hin paint ngan brush.", 
        "vocabulary": "ngan", 
        "difficulty": 3, 
        "response_time": 0
    },

    {
        "id": 173, 
        "type": "Lesson", 
        "question": "'Tagpira?' means 'How much?' in Waray, used to ask for prices.", 
        "audio_file": "tagpira.mp3", 
        "image": "tagpira.jpg", 
        "answer": None, 
        "vocabulary": "Tagpira", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 174, 
        "type": "Pronunciation", 
        "question": "How do you pronounce 'Tagpira'?",
        "audio_file": "tagpira.mp3", 
        "accuracy": None, 
        "accuracy_threshold": 0.8, 
        "vocabulary": "Tagpira",
        "difficulty": 1, 
        "response_time": None
    },
    {
        "id": 175, 
        "type": "Translate Sentence", 
        "question": "Translate this: How much is this?", 
        "choices": ["Tagpira iton?", "Tagpira ini?"], 
        "correct_answer": "Tagpira ini?", 
        "vocabulary": "Tagpira", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 176, 
        "type": "Lesson", 
        "question": "'Tagpira nga tanan?' means 'How much for all of it?' or 'What's the total?'", 
        "audio_file": "tagpira_nga_tanan.mp3", 
        "image": "tagpira_nga_tanan.jpg", 
        "answer": None, 
        "vocabulary": "Tagpira nga tanan", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 177, 
        "type": "Translate Sentence", 
        "question": "Translate this: How much for everything?",
        "choices": ["Tagpira iton?", "Tagpira nga tanan?"], 
        "correct_answer": "Tagpira nga tanan?", 
        "vocabulary": "Tagpira nga tanan", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 178, 
        "type": "Translate Sentence", 
        "question": "You've picked up items. How do you ask the total price?", 
        "choices": ["Tagpira nga tanan?", "Tagpira la?"], 
        "correct_answer": "Tagpira nga tanan?", 
        "vocabulary": "Tagpira nga tanan", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 179, 
        "type": "Translate Sentence", 
        "question": "After picking up groceries, how would you ask the cashier?", 
        "choices": ["Tagpira nga tanan?", "Tagpira it bugas?"], 
        "correct_answer": "Tagpira nga tanan?", 
        "vocabulary": "Tagpira nga tanan", 
        "difficulty": 3, 
        "response_time": 0
    },
    ],
    "Lesson 3": [
    {
        "id": 180, 
        "type": "Lesson", 
        "question": "'Gusto ko ini' means 'I want this' in Waray. Use it when you like or want something.", 
        "audio_file": "gusto_ko_ini.mp3", 
        "image": "gusto_ko.jpg", 
        "answer": None, 
        "vocabulary": "Gusto ko ini", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 181, 
        "type": "Translate Sentence", 
        "question": "Translate this: What is that? I want that!", 
        "choices": ["Ano iton? Gusto ko iton!", "Ano ini? Gusto ko ini!"], 
        "correct_answer": "Ano iton? Gusto ko iton!", 
        "vocabulary": "Gusto ko iton", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 182, 
        "type": "Translate Sentence", 
        "question": "Translate this: I want this bag. How much is this?", 
        "choices": ["Gusto ko ini nga bag. Tagpira ini?", "Gusto ko iton nga bag. Kayano ini?"], 
        "correct_answer": "Gusto ko ini nga bag. Tagpira ini?", 
        "vocabulary": "Gusto ko ini", 
        "difficulty": 4, 
        "response_time": 0
    },

    {
        "id": 183, 
        "type": "Lesson", 
        "question": "Nadiri ako means 'I don't like' or 'I refuse'.", 
        "audio_file": "nadiri.mp3", 
        "image": "nadiri.jpg", 
        "answer": None, 
        "vocabulary": "Nadiri", 
        "difficulty": None,
        "response_time": None
    },
    {
        "id": 184, 
        "type": "Image Picker", 
        "question": "Nadiri", 
        "choices": ["fish_dish.jpg", "happy_face.jpg", "thumbs_down.jpg"], 
        "correct_answer": "thumbs_down.jpg", 
        "vocabulary": "Nadiri", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 185, 
        "type": "Translate Sentence", 
        "question": "You’re at a market and offered a fish dish you don’t like. What do you say?", 
        "choices": ["Nadiri ako hin isda.", "Tagpira an isda?"], 
        "correct_answer": "Nadiri ako hin isda.", 
        "vocabulary": "Nadiri", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 186, 
        "type": "Translate Sentence", 
        "question": "Vendor: Maupay nga aga, Maya! May halo-halo didi. Gusto mo?\nMaya: _____", 
        "choices": ["Nadiri ako hin halo-halo.", "Mapalit ako hin halo-halo."], 
        "correct_answer": "Nadiri ako hin halo-halo.", 
        "vocabulary": "Nadiri", 
        "difficulty": 4, 
        "response_time": 0
    },
    {
        "id": 187, 
        "type": "Lesson", 
        "question": "Ayaw nala means 'Nevermind' or 'Huwag nalang' in Filipino.", 
        "audio_file": "ayaw_nala.mp3", 
        "image": "ayaw_nala.jpg", 
        "answer": None, 
        "vocabulary": "Ayaw nala", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 188, 
        "type": "True or False", 
        "question": "Ayaw nala translates to 'Huwag nalang' in Filipino.", 
        "choices": ["True", "False"], 
        "correct_answer": "True", 
        "vocabulary": "Ayaw nala", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 189, 
        "type": "Translate Sentence", 
        "question": "You change your mind. What should you tell the vendor?", 
        "choices": ["Palit la.", "Ayaw nala."], 
        "correct_answer": "Ayaw nala.", 
        "vocabulary": "Ayaw nala", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 190, 
        "type": "Translate Sentence", 
        "question": "Vendor: Mapalit ka pa?\nNero: ________", 
        "choices": ["Ayaw nala. Damo nga salamat!", "Mapalit pa. Salamat!"], 
        "correct_answer": "Ayaw nala. Damo nga salamat!", 
        "vocabulary": "Ayaw nala", 
        "difficulty": 4, 
        "response_time": 0
    },
    ],
    "Lesson 4": [
    {
        "id": 191, 
        "type": "Lesson", 
        "question": "Adi means 'here' and is used when handing something over.", 
        "audio_file": "adi.mp3", 
        "image": "adi.jpg", 
        "answer": None, 
        "vocabulary": "Adi", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 192, 
        "type": "Word Select", 
        "question": "What does 'Adi' mean?", 
        "choices": ["There", "Here", "Thank you"], 
        "correct_answer": "Here", 
        "vocabulary": "Adi", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 193, 
        "type": "Pronunciation", 
        "question": "How do you pronounce 'Adi'?", 
        "audio_file": "adi.mp3", 
        "accuracy": None, 
        "accuracy_threshold": 0.8, 
        "vocabulary": "Adi", 
        "difficulty": 1, 
        "response_time": None
    },
    {
        "id": 194, 
        "type": "Word Select", 
        "question": "Midi: Tag-piso it kendi. You hand a five-peso coin. What do you say?", 
        "choices": ["Adi", "Tagpira", "Nadiri ako"], 
        "correct_answer": "Adi", 
        "vocabulary": "Adi", 
        "difficulty": 4, 
        "response_time": 0
    },
    {
        "id": 195, 
        "type": "Word Select", 
        "question": "Vendor: 20 pesos. Rosa:__________", 
        "choices": ["Adi", "Ito", "Sige"], 
        "correct_answer": "Adi", 
        "vocabulary": "Adi", 
        "difficulty": 5, 
        "response_time": 0
    },
    {
        "id": 196, 
        "type": "Lesson", 
        "question": "Bayad / Sukli: 'Bayad' means payment and 'sukli' means change.", 
        "audio_file": "bayad_sukli.mp3", 
        "image": "bayad_sukli.jpg", 
        "answer": None, 
        "vocabulary": "Bayad / Sukli", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 197, 
        "type": "Translate Sentence", 
        "question": "Translate this: Here is my payment.", 
        "choices": ["Adi it akon bayad.", "Maupay it akon bayad."], 
        "correct_answer": "Adi it akon bayad.", 
        "vocabulary": "Bayad", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 198, 
        "type": "Translate Sentence", 
        "question": "You want to give your payment. What do you say?", 
        "choices": ["Waray it akon bayad.", "Adi it akon bayad."], 
        "correct_answer": "Adi it akon bayad.", 
        "vocabulary": "Bayad", 
        "difficulty": 3, 
        "response_time": 0
    },
    {
        "id": 199, 
        "type": "Translate Sentence", 
        "question": "You have not been given your change. What would you ask?", 
        "choices": ["Hino it akon sukli?", "Hain it akon sukli?"], 
        "correct_answer": "Hain it akon sukli?", 
        "vocabulary": "Sukli", 
        "difficulty": 4, 
        "response_time": 0
    },
    ],
    "Lesson 5": [
    {
        "id": 200, 
        "type": "Lesson", 
        "question": "Mayda (short for may-ada) means 'there is' or 'have'.", 
        "audio_file": "mayda.mp3", 
        "image": "mayda.jpg", 
        "answer": None, 
        "vocabulary": "Mayda", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 201, 
        "type": "True or False", 
        "question": "'Mayda' functions like 'Mayroon' in Filipino.", 
        "choices": ["True", "False"], 
        "correct_answer": "True", 
        "vocabulary": "Mayda", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 202, 
        "type": "Word Select", 
        "question": "Translate to English: Mayda", 
        "choices": ["want", "need", "have"], 
        "correct_answer": "have", 
        "vocabulary": "Mayda", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 203, 
        "type": "Translate Sentence", 
        "question": "You want to know if the bookstore sells notebooks. What should you ask?", 
        "choices": ["Mayda notebook?", "Tagpira it notebook?"], 
        "correct_answer": "Mayda notebook?", 
        "vocabulary": "Mayda", 
        "difficulty": 3, 
        "response_time": 0
    },
    {
        "id": 204, 
        "type": "Lesson", 
        "question": "Amo la means 'That's all' in English. Use it when you're finished selecting items.", 
        "audio_file": "amo_la.mp3", 
        "image": "amo_la.jpg", 
        "answer": None, 
        "vocabulary": "Amo la", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 205, 
        "type": "True or False", 
        "question": "'Amo la' is used when you're done selecting items to buy.", 
        "choices": ["True", "False"], 
        "correct_answer": "True", 
        "vocabulary": "Amo la", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 206, 
        "type": "Word Select", 
        "question": "Translate to Waray: That's all", 
        "choices": ["Mao ra", "Amo la", "Andu man"], 
        "correct_answer": "Amo la", 
        "vocabulary": "Amo la", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 207, 
        "type": "Translate Sentence", 
        "question": "How would you tell the vendor that's all you want to buy?", 
        "choices": ["Amo la.", "Ayaw nala."], 
        "correct_answer": "Amo la.", 
        "vocabulary": "Amo la", 
        "difficulty": 3, 
        "response_time": 0
    },
    {
        "id": 208, 
        "type": "Lesson", 
        "question": "'Pwede tumawad?' means 'Can I ask for a discount?'. Use it to negotiate prices.", 
        "audio_file": "pwede_tumawad.mp3", 
        "image": "pwede_tumawad.jpg", 
        "answer": None, 
        "vocabulary": "Pwede tumawad", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 209, 
        "type": "True or False", 
        "question": "'Pwede tumawad?' translates to 'Can I ask for a discount?'.", 
        "choices": ["True", "False"], 
        "correct_answer": "True", 
        "vocabulary": "Pwede tumawad", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 210, 
        "type": "Translate Sentence", 
        "question": "How would you ask for a discount at the market?", 
        "choices": ["Pwede tumawad?", "Pwede maluoy?"], 
        "correct_answer": "Pwede tumawad?", 
        "vocabulary": "Pwede tumawad", 
        "difficulty": 2, 
        "response_time": 0
    },
    ]
}

module_4 = {

    "Lesson 1": [
    {
        "id": 211, 
        "type": "Lesson", 
        "question": "Kaon is the root word that means 'to eat' in Waray. It is the same as 'Kain' in Filipino.", 
        "audio_file": "kaon.mp3", 
        "image": "kaon.jpg", 
        "answer": None, 
        "vocabulary": "Kaon", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 212, 
        "type": "Cultural Trivia", 
        "question": "'Kaon' in Waray is the same as 'kain' in Filipino—just flip the I into an O!", 
        "choices": ["Trivia only"], 
        "correct_answer": "Trivia only", 
        "vocabulary": "Kaon", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 213, 
        "type": "Pronunciation", 
        "question": "How do you pronounce 'Kaon'?", 
        "audio_file": "kaon.mp3", 
        "accuracy": None, 
        "accuracy_threshold": 0.8, 
        "vocabulary": "Kaon", 
        "difficulty": 1, 
        "response_time": None
    },
    {
        "id": 214, 
        "type": "Image Picker", 
        "question": "Kaon", 
        "choices": ["eating.jpg", "food.jpg", "table.jpg"], 
        "correct_answer": "eating.jpg", 
        "vocabulary": "Kaon", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 215, 
        "type": "Translate Sentence", 
        "question": "How would you say, 'Let's eat.'?", 
        "choices": ["Kaon kita.", "Pagkaon kita."], 
        "correct_answer": "Kaon kita.", 
        "vocabulary": "Kaon", 
        "difficulty": 3, 
        "response_time": 0
    },

    {
        "id": 216, 
        "type": "Lesson", 
        "question": "Pagkaon means 'food' and refers to what you eat. It is the same as 'Pagkain' in Filipino.", 
        "audio_file": "pagkaon.mp3", 
        "image": "pagkaon.jpg", 
        "answer": None, 
        "vocabulary": "Pagkaon", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 217, 
        "type": "Word Select", 
        "question": "Translate to Waray: food", 
        "choices": ["pagkaon", "kaon", "lakat"], 
        "correct_answer": "pagkaon", 
        "vocabulary": "Pagkaon", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 218, 
        "type": "Image Picker", 
        "question": "Pagkaon", 
        "choices": ["rice.jpg", "fish.jpg", "meal.jpg"], 
        "correct_answer": "meal.jpg", 
        "vocabulary": "Pagkaon", 
        "difficulty": 3, 
        "response_time": 0
    },
    {
        "id": 219, 
        "type": "Word Select", 
        "question": "What is the correct meaning of pagkaon?", 
        "choices": ["Pagkaon = Eat", "Pagkaon = Food"], 
        "correct_answer": "Pagkaon = Food", 
        "vocabulary": "Pagkaon", 
        "difficulty": 3, 
        "response_time": 0
    },

    {
        "id": 220, 
        "type": "Lesson", 
        "question": "Pangaon means the act of eating or the time for eating. 'Pangaon kita' is the Waray version for 'Tara, kain!' or 'Let's eat!'", 
        "audio_file": "pangaon.mp3", 
        "image": "pangaon.jpg", 
        "answer": None, 
        "vocabulary": "Pangaon", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 221, 
        "type": "Word Select", 
        "question": "Translate to Waray: mealtime", 
        "choices": ["kaon", "pagkaon", "pangaon"], 
        "correct_answer": "pangaon", 
        "vocabulary": "Pangaon", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 222, 
        "type": "Translate Sentence", 
        "question": "Which sentence is appropriate to say before eating?", 
        "choices": ["Pagkaon na kita!", "Pangaon na kita!"], 
        "correct_answer": "Pangaon na kita!", 
        "vocabulary": "Pangaon", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 223, 
        "type": "Translate Sentence", 
        "question": "How would you invite your friend to eat lunch with you?",
        "choices": ["Pangaon kita!", "Maupay nga aga!"], 
        "correct_answer": "Pangaon kita!", 
        "vocabulary": "Pangaon", 
        "difficulty": 3, 
        "response_time": 0
    },
    ],
    "Lesson 2": [
    {
        "id": 224, 
        "type": "Lesson", 
        "question": "'Kumaon' means 'ate,' and is the past tense of 'kaon'.", 
        "audio_file": "kumaon.mp3", 
        "image": "kumaon.jpg", 
        "answer": None, 
        "vocabulary": "kumaon", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 225, 
        "type": "Cultural Trivia", 
        "question": "In Waray, 'kumaon' uses the 'um' infix just like in Filipino grammar—showing shared root structures!", 
        "choices": ["Trivia only"], 
        "correct_answer": "Trivia only", 
        "vocabulary": "kumaon", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 226, 
        "type": "Word Select", 
        "question": "Translate to Waray: ate", 
        "choices": ["kumaon", "pagkaon", "pangaon"], 
        "correct_answer": "kumaon", 
        "vocabulary": "kumaon", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 227, 
        "type": "Translate Sentence", 
        "question": "How would you say, 'Have you eaten?' in Waray?", 
        "choices": ["Kaon ka na?", "Kumaon ka na?"], 
        "correct_answer": "Kumaon ka na?", 
        "vocabulary": "kumaon", 
        "difficulty": 3, 
        "response_time": 0
    },

    {
        "id": 228, 
        "type": "Lesson", 
        "question": "'Magutom na' is used to express that you're hungry. 'Ma-' shows a feeling or condition.", 
        "audio_file": "magutom.mp3", 
        "image": "magutom.jpg", 
        "answer": None, 
        "vocabulary": "magutom", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 229, 
        "type": "Image Picker", 
        "question": "magutom", 
        "choices": ["hungry.jpg", "full.jpg", "cooking.jpg"], 
        "correct_answer": "hungry.jpg", 
        "vocabulary": "magutom", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 230, 
        "type": "Translate Sentence", 
        "question": "Translate to Waray: I'm hungry.", 
        "choices": ["Magutom na.", "Kaon kita."], 
        "correct_answer": "Magutom na.", 
        "vocabulary": "magutom", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 231, 
        "type": "Translate Sentence", 
        "question": "You want to tell a friend you’re getting hungry. What do you say?", 
        "choices": ["Magutom na.", "May pagkaon na."], 
        "correct_answer": "Magutom na.", 
        "vocabulary": "magutom", 
        "difficulty": 3, 
        "response_time": 0
    },

    {
        "id": 232, 
        "type": "Lesson", 
        "question": "'Marasa' means delicious or tasty in Waray. You use it to describe food you really like.", 
        "audio_file": "marasa.mp3", 
        "image": "marasa.jpg", 
        "answer": None, 
        "vocabulary": "marasa", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 233, 
        "type": "Pronunciation", 
        "question": "Pronounce 'marasa'", 
        "audio_file": "marasa.mp3", 
        "accuracy": None, 
        "accuracy_threshold": 0.8, 
        "vocabulary": "marasa", 
        "difficulty": 2, 
        "response_time": None
    },
    {
        "id": 234, 
        "type": "Translate Sentence", 
        "question": "Alona: Kaon na kita!\nWhat would you say after eating something tasty?", 
        "choices": ["Marasa!", "Magutom!"], 
        "correct_answer": "Marasa!", 
        "vocabulary": "marasa", 
        "difficulty": 3, 
        "response_time": 0
    },
    {
        "id": 235, 
        "type": "Translate Sentence", 
        "question": "How would you say, 'The food is tasty.'?", 
        "choices": ["Mapaso it pagkaon.", "Marasa it pagkaon."], 
        "correct_answer": "Marasa it pagkaon.", 
        "vocabulary": "marasa", 
        "difficulty": 4, 
        "response_time": 0
    },
    {
        "id": 236, 
        "type": "Translate Sentence", 
        "question": "You want to compliment the vendor’s adobo dish. What can you say?", 
        "choices": ["Pagkaon ini nga adobo!", "Marasa ini nga adobo!"], 
        "correct_answer": "Marasa ini nga adobo!", 
        "vocabulary": "marasa", 
        "difficulty": 5, 
        "response_time": 0
    },
    ],
    "Lesson 3": [
    {
        "id": 237, 
        "type": "Lesson", 
        "question": "Gusto ko ini tilawon means 'I want to try this'. 'Tilawon' is to try or taste food.", 
        "audio_file": "gusto_tilawon.mp3", 
        "image": "tilawon.jpg", 
        "answer": None, 
        "vocabulary": "tilawon", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 238, 
        "type": "True or False", 
        "question": "'Gusto ko ini tilawon' is what you say when you want to taste something.", 
        "choices": ["True", "False"], 
        "correct_answer": "True", 
        "vocabulary": "tilawon", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 239, 
        "type": "Translate Sentence", 
        "question": "Translate this: I want to taste this.", 
        "choices": ["Gusto ko iton tilawon.", "Gusto ko ini tilawon."], 
        "correct_answer": "Gusto ko ini tilawon.", 
        "vocabulary": "tilawon", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 240, 
        "type": "Translate Sentence", 
        "question": "You point to a dish and want to try it. What do you say?", 
        "choices": ["Gusto ko ini tilawon.", "Gusto ko ini bayad."], 
        "correct_answer": "Gusto ko ini tilawon.", 
        "vocabulary": "tilawon", 
        "difficulty": 3, 
        "response_time": 0
    },

    {
        "id": 241, 
        "type": "Lesson", 
        "question": "'Ano it imo gusto kaunon?' means 'What do you want to eat?'", 
        "audio_file": "kaunon.mp3", 
        "image": "kaunon.jpg", 
        "answer": None, 
        "vocabulary": "kaunon", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 242, 
        "type": "True or False", 
        "question": "'Ano it imo gusto kaunon?' is used to ask someone about their food preference.", 
        "choices": ["True", "False"], 
        "correct_answer": "True", 
        "vocabulary": "kaunon", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 243, 
        "type": "Translate Sentence", 
        "question": "How do you ask Anya what she wants to eat?", 
        "choices": ["Ano it imo gusto tilawon?", "Ano it imo gusto kaunon?"], 
        "correct_answer": "Ano it imo gusto kaunon?", 
        "vocabulary": "kaunon", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 244, 
        "type": "Translate Sentence", 
        "question": "You're at a restaurant with friends. Ask what they want to eat.", 
        "choices": ["Ano it iyo gusto kaunon?", "Ano it iyo gusto tilawon?"], 
        "correct_answer": "Ano it iyo gusto kaunon?", 
        "vocabulary": "kaunon", 
        "difficulty": 3, 
        "response_time": 0
    },

    {
        "id": 245, 
        "type": "Lesson", 
        "question": "'Maaro!' means 'Can I have some?'—used when politely requesting food.", 
        "audio_file": "maaro.mp3", 
        "image": "maaro.jpg", 
        "answer": None, 
        "vocabulary": "maaro", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 246, 
        "type": "True or False", 
        "question": "'Maaro!' is used to ask for a share of something.", 
        "choices": ["True", "False"], 
        "correct_answer": "True",
        "vocabulary": "maaro", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 247, 
        "type": "Image Picker", 
        "question": "Maaro!", 
        "choices": ["request.jpg", "no.jpg", "plate.jpg"], 
        "correct_answer": "request.jpg", 
        "vocabulary": "maaro", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 248, 
        "type": "Translate Sentence", 
        "question": "How would you ask for bread (tinapay)?", 
        "choices": ["Maaro tinapay!", "Matilaw tinapay!"], 
        "correct_answer": "Maaro tinapay!", 
        "vocabulary": "maaro", 
        "difficulty": 3, 
        "response_time": 0
    },
    ],
    "Lesson 4": [
    {
        "id": 249, 
        "type": "Lesson", 
        "question": "'Mapaalayon it (item)' means 'May I have (item), please'. Used for polite requests.", 
        "audio_file": "mapaalayon.mp3", 
        "image": "mapaalayon.jpg", 
        "answer": None, 
        "vocabulary": "mapaalayon", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 250, 
        "type": "True or False", 
        "question": "'Mapaalayon' is a polite way to request for something.", 
        "choices": ["True", "False"], 
        "correct_answer": "True", 
        "vocabulary": "mapaalayon", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 251, 
        "type": "Image Picker", 
        "question": "Mapaalayon it plato", 
        "choices": ["plate.jpg", "cup.jpg", "bottle.jpg"], 
        "correct_answer": "plate.jpg", 
        "vocabulary": "mapaalayon", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 252, 
        "type": "Translate Sentence", 
        "question": "Ask politely for the glass of water across the table.", 
        "choices": ["Mapaalayon it tubig.", "Mayda tubig?"], 
        "correct_answer": "Mapaalayon it tubig.", 
        "vocabulary": "mapaalayon", 
        "difficulty": 3, 
        "response_time": 0
    },

    {
        "id": 253, 
        "type": "Lesson", 
        "question": "'Salamat ha pagkaon' means 'Thank you for the food'.", 
        "audio_file": "salamat_pagkaon.mp3", 
        "image": "salamat.jpg", 
        "answer": None, 
        "vocabulary": "salamat ha pagkaon", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 254, 
        "type": "True or False", 
        "question": "'Salamat ha pagkaon' means 'Thank you for the food' in Waray.", 
        "choices": ["True", "False"], 
        "correct_answer": "True", 
        "vocabulary": "salamat ha pagkaon", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 255, 
        "type": "Translate Sentence", 
        "question": "How would you thank someone for giving you food?", 
        "choices": ["Salamat ha pagkaon.", "Maupay nga pagkaon."], 
        "correct_answer": "Salamat ha pagkaon.", 
        "vocabulary": "salamat ha pagkaon", 
        "difficulty": 2, 
        "response_time": 0
    },

    {
        "id": 256, 
        "type": "Lesson", 
        "question": "'Busog na ak' means 'I'm full already'.", 
        "audio_file": "busog_na_ak.mp3", 
        "image": "busog.jpg", 
        "answer": None, 
        "vocabulary": "busog na ak", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 257, 
        "type": "Word Select", 
        "question": "Translate to Waray: I'm full", 
        "choices": ["Busog ak", "Gutom ak", "Busog ako"], 
        "correct_answer": "Busog ak", 
        "vocabulary": "busog", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 258, 
        "type": "Image Picker", 
        "question": "Busog na ak", 
        "choices": ["full.jpg", "hungry.jpg", "eating.jpg"], 
        "correct_answer": "full.jpg", 
        "vocabulary": "busog", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 259, 
        "type": "Translate Sentence", 
        "question": "You're full after a meal. What do you say?", 
        "choices": ["Gutom pa ak.", "Busog na ak."], 
        "correct_answer": "Busog na ak.", 
        "vocabulary": "busog", 
        "difficulty": 3, 
        "response_time": 0
    },
    ],
    "Lesson 5": [
    {
        "id": 260, 
        "type": "Lesson", 
        "question": "'Adi it pagkaon' means 'Here is the food'. Used when serving meals.", 
        "audio_file": "adi_it_pagkaon.mp3", 
        "image": "adi_pagkaon.jpg", 
        "answer": None, 
        "vocabulary": "Adi it pagkaon", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 261, 
        "type": "True or False", 
        "question": "'Adi it pagkaon' is what you say when handing food to someone.", 
        "choices": ["True", "False"], 
        "correct_answer": "True", 
        "vocabulary": "Adi it pagkaon", 
        "difficulty": 1, 
        "response_time": 0
    },
    {
        "id": 262, 
        "type": "Image Picker", 
        "question": "Adi it pagkaon", 
        "choices": ["serving.jpg", "eating.jpg", "menu.jpg"], 
        "correct_answer": "serving.jpg", 
        "vocabulary": "Adi it pagkaon", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 263, 
        "type": "Translate Sentence", 
        "question": "Translate this: Here is the food.", 
        "choices": ["Adto is pagkaon.", "Adi it pagkaon."], 
        "correct_answer": "Adi it pagkaon.", 
        "vocabulary": "Adi it pagkaon", 
        "difficulty": 3, 
        "response_time": 0
    },

    {
        "id": 264, 
        "type": "Lesson", 
        "question": "'Mapaso' means 'hot' (like food that is temperature hot).", 
        "audio_file": "mapaso.mp3", 
        "image": "mapaso.jpg", 
        "answer": None, 
        "vocabulary": "Mapaso", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 265, 
        "type": "Image Picker", 
        "question": "Mapaso", 
        "choices": ["hot_soup.jpg", "cold_water.jpg", "ice.jpg"], 
        "correct_answer": "hot_soup.jpg", 
        "vocabulary": "Mapaso", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 266, 
        "type": "Word Select", 
        "question": "Translate to Waray: hot", 
        "choices": ["mahagkot", "mapaso", "matilaw"], 
        "correct_answer": "mapaso", 
        "vocabulary": "Mapaso", 
        "difficulty": 3, 
        "response_time": 0
    },

    {
        "id": 267, 
        "type": "Lesson", 
        "question": "'Mahagkot' means 'cold' in Waray. It is the opposite of 'mapaso'.", 
        "audio_file": "mahagkot.mp3", 
        "image": "mahagkot.jpg", 
        "answer": None, 
        "vocabulary": "Mahagkot", 
        "difficulty": None, 
        "response_time": None
    },
    {
        "id": 268, 
        "type": "Image Picker", 
        "question": "Mahagkot", 
        "choices": ["ice.jpg", "soup.jpg", "coffee.jpg"], 
        "correct_answer": "ice.jpg", 
        "vocabulary": "Mahagkot", 
        "difficulty": 2, 
        "response_time": 0
    },
    {
        "id": 269, 
        "type": "Word Select", 
        "question": "Translate to Waray: cold", 
        "choices": ["mapaso", "mahagkot", "maopay"], 
        "correct_answer": "mahagkot", 
        "vocabulary": "Mahagkot", 
        "difficulty": 3, 
        "response_time": 0
    }
    ]
}
    
module_bank = {
    1: module_1,
    2: module_2,
    3: module_3,
    4: module_4,
}

achievement_bank = {
    "achv_1": {
        "id": 1,
        "name": "First Level Completed",
        "description": "Complete the first level.",
        "icon": "assets/achievements/level_completed.png",
        "completed": False
    },
    "achv_2": {
        "id": 2,
        "name": "First Module Completed",
        "description": "Complete the first module.",
        "icon": "assets/achievements/module_completed.png",
        "completed": False
    },
    "achv_3": {
        "id": 3,
        "name": "All Modules Completed",
        "description": "Complete all modules.",
        "icon": "assets/achievements/all_modules_completed.png",
        "completed": False
    },
    "achv_4": {
        "id": 4,
        "name": "All Achievements Completed",
        "description": "Complete all levels.",
        "icon": "assets/achievements/all_levels_completed.png",
        "completed": False
    }
}

# Updated vocabulary dictionaries for Module 2
module_2_vocab = {
    "Hain": "Where (present)",
    "Makain": "Where (future)",
    "Lakat": "Walk",
    "Pakadto": "Go (future tense)",
    "Para": "Stop the jeepney",
    "Tag-pira": "How much",
    "Alayon": "Please",
    "Hirayo": "Far",
    "Hirani": "Near",
    "Aadi": "Here",
    "Yana": "Right now/today",
    "Buwas": "Tomorrow",
    "Niyan": "Later",
    "Kakulop": "Yesterday",
    "San-o": "When",
    "Hinay": "Slow/take care"
}

# Updated module names and descriptions
eng_name_bank = {
    1: "Greetings and Introductions",
    2: "Transportation and Getting Around",
    3: "Shopping and Buying",
    4: "Ordering food",
    # Add more names
}

waray_name_bank = {
    1: "Kamustahay!",
    2: "Transportasyon ngan Paglakat",
    3: "Pagbakal ngan Pag-order",
    4: "Pag-order hin pagkaon",
    # Add more names
}

desc_bank = {
    1: "Learn basic greetings and introductions in Waray.",
    2: "Learn how to ask for directions and navigate transportation in Waray.",
    3: "Learn how to shop and buy items in Waray.",
    4: "Learn how to order food in Waray.",
    # Add more descriptions
}

word_library = {
    # Module 1 Vocabulary
    "Maupay nga aga": "Good morning",
    "gihapon": "too/also",
    "kamusta ka": "How are you?",
    "ikaw?": "How about you?",
    "la": "just/only",
    "okay la ako": "I'm just okay",
    "kulop": "afternoon",
    "Maupay nga kulop": "Good afternoon",
    "diri": "no/not",
    "It": "The",
    "gab-i": "night",
    "Maupay nga gab-i": "Good evening",
    "ano it imo ngaran?": "What is your name?",
    "ngaran": "name",
    "ako hi": "I am",
    "damo nga salamat": "Thank you very much",
    "damo": "many/a lot",
    "salamat": "thanks",
    "waray sapayan": "You're welcome",
    "pasaylo-a ako": "I'm sorry",
    "maaram ka mag-english": "Do you know how to speak English?",
    "maaram": "to know",
    "diri ako makarit ha waray": "I'm not good at Waray",
    "makarit": "good at/skilled",
    "ambot": "I don't know",

    # Module 2 Vocabulary
    "Hain": "Where (present)",
    "Hain ka?": "Where are you?",
    "Makain": "Where (future)",
    "Makain ka?": "Where are you going?",
    "Lakat": "Walk",
    "Lakat kita": "Let's go",
    "Pakadto": "Go (future tense)",
    "Pakadto kita ha": "Let's go to",
    "Para": "Stop the jeepney",
    "Tag-pira": "How much",
    "Tagpira it pasahe": "How much is the fare",
    "Alayon": "Please",
    "Hirayo": "Far",
    "Hirani": "Near",
    "Aadi": "Here",
    "Yana": "Right now/today",
    "Buwas": "Tomorrow",
    "Niyan": "Later",
    "Kakulop": "Yesterday",
    "San-o": "When",
    "Hinay": "Slow/take care",

    # Module 3 Vocabulary
    "Maupay": "Good/Hey (to call vendor)",
    "Ano ini": "What is this?",
    "ini": "this",
    "Ano iton": "What is that?",
    "iton": "that",
    "Mapalit ako hin": "I want to buy",
    "Mapalit": "to buy",
    "ngan": "and",
    "Tagpira": "How much?",
    "Tagpira nga tanan": "How much for all of it?",
    "Gusto ko ini": "I want this",
    "Gusto ko iton": "I want that",
    "Nadiri": "I don't like/I refuse",
    "Ayaw nala": "Nevermind",
    "Adi": "here (when handing)",
    "Bayad": "payment",
    "Sukli": "change (money)",
    "Mayda": "there is/have",
    "Amo la": "That's all",
    "Pwede tumawad": "Can I ask for a discount?",

    # Module 4 Vocabulary
    "Kaon": "to eat",
    "Pagkaon": "food",
    "Pangaon": "mealtime/act of eating",
    "kumaon": "ate (past tense)",
    "magutom": "hungry",
    "marasa": "delicious/tasty",
    "tilawon": "to try/taste",
    "kaunon": "to eat (future)",
    "maaro": "Can I have some?",
    "mapaalayon": "May I have, please",
    "salamat ha pagkaon": "Thank you for the food",
    "busog na ak": "I'm full already",
    "busog": "full (after eating)",
    "Adi it pagkaon": "Here is the food",
    "Mapaso": "hot (temperature)",
    "Mahagkot": "cold (temperature)"
}


# Add image attributes wherever applicable depending on gui design

