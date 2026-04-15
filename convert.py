import codecs
with codecs.open('data.json', 'r', 'utf-16le') as f1:
    data = f1.read()
with codecs.open('data_utf8.json', 'w', 'utf-8') as f2:
    f2.write(data)
