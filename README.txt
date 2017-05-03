[daniel.py]  For testing simple files
  Can be tested with the following command:
    python daniel.py LANGUAGE FILE
  Example :
    python daniel.py Indonesian some_document_in_indonesian.html

[process_corpus.py]  For processing a corpus :
  The command :
    python process_corpus.py -c JSON_FILE
  Needs a JSON file  (see below for the format)

[evaluate.py] For evaluating results
  Compares the content of a groundtruth JSOn file and an output from daniel
    python evaluate.py GROUNDTRUTH DANIEL_OUTPUT

[The JSON format]
  A dictionnary where each key is the ID of a document
  The value is a dictionnary with informations on the document:  
    - mandatory information :
      - file path
    - useful informations (by decreasing importance) :
      - source
      - language
      - url
      - comment
    -information for evaluation :
      - annotations
    See docs/Indonesian_GL.json for an example

