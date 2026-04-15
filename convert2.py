import codecs
with codecs.open('data_utf8.json', 'r', 'utf-8-sig') as f1:
    data = f1.read()
with codecs.open('data_utf8_nobom.json', 'w', 'utf-8') as f2:
    f2.write(data)
