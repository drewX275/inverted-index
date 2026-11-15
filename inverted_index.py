#-------------------------------------------------------------------------
# AUTHOR: Andrew Mazmanian
# FILENAME: inverted_index.py
# SPECIFICATION: maintains the documents and inverted_index collections of
#                the assignment3 MongoDB database as documents are
#                inserted, updated, and deleted. Each term's postings
#                (docId, tf) are kept in sync with the documents, new
#                terms are created, terms with no postings are removed,
#                and both collections are printed at the end.
# FOR: CS 4250 - Assignment #3
# TIME SPENT: 5 hours
#-------------------------------------------------------------------------

# Importing Python libraries
from pymongo import MongoClient

# Connecting to MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Accessing the database and collections
db = client["assignment3"]
documents = db["documents"]
inverted_index = db["inverted_index"]


#-------------------------------------------------------------------------
# FUNCTION: getTermFrequencies
# SPECIFICATION: receives a text and returns the frequency of each term
#-------------------------------------------------------------------------
def getTermFrequencies(text):

    # Converting text to lowercase
    text = text.lower()


    # Removing punctuation
    text = "".join(character for character in text if character.isalnum() or character.isspace())


    # Splitting the text into terms
    terms = text.split()


    # Returning the term frequencies
    termFrequencies = {}
    for term in terms: termFrequencies[term] = termFrequencies.get(term, 0) + 1
    return termFrequencies



#-------------------------------------------------------------------------
# FUNCTION: addPosting
# SPECIFICATION: adds a posting to an existing term or creates a new term
#-------------------------------------------------------------------------
def addPosting(term, docId, tf):

    # Searching for the term in the inverted index
    termDocument = inverted_index.find_one({"term": term})


    # Creating a new term if it does not exist
    if termDocument is None: inverted_index.insert_one({"term": term, "postings": [{"docId": docId, "tf": tf}]})


    # Adding a posting if the term already exists
    else: inverted_index.update_one({"term": term}, {"$push": {"postings": {"docId": docId, "tf": tf}}})


#-------------------------------------------------------------------------
# FUNCTION: removePosting
# SPECIFICATION: removes a document posting from a term and deletes the
#                term if its postings list becomes empty
#-------------------------------------------------------------------------
def removePosting(term, docId):

    # Removing the posting from the term
    inverted_index.update_one({"term": term}, {"$pull": {"postings": {"docId": docId}}})


    # Retrieving the term after removing the posting
    termDocument = inverted_index.find_one({"term": term})


    # Deleting the term if its postings list is empty
    if termDocument is not None and len(termDocument["postings"]) == 0: inverted_index.delete_one({"term": term})



#-------------------------------------------------------------------------
# FUNCTION: insertDocument
# SPECIFICATION: inserts a document and updates the inverted index
#-------------------------------------------------------------------------
def insertDocument(document):

    # Inserting the document into the documents collection
    documents.insert_one(document)


    # Obtaining the term frequencies
    termFrequencies = getTermFrequencies(document["text"])


    # Updating the inverted index
    for term, tf in termFrequencies.items(): addPosting(term, document["_id"], tf)


#-------------------------------------------------------------------------
# FUNCTION: updateDocument
# SPECIFICATION: updates a document and makes the corresponding changes
#                to the inverted index
#-------------------------------------------------------------------------
def updateDocument(docId, newText):

    # Retrieving the current document
    currentDocument = documents.find_one({"_id": docId})


    # Obtaining the old and new term frequencies
    oldFrequencies = getTermFrequencies(currentDocument["text"])
    newFrequencies = getTermFrequencies(newText)


    # Processing terms that existed in the old document
    for term, oldTf in oldFrequencies.items():
        if term not in newFrequencies: removePosting(term, docId) # term no longer occurs in the document: remove its posting
        elif newFrequencies[term] != oldTf:
            # term still occurs but with a different tf: replace its posting
            inverted_index.update_one({"term": term}, {"$pull": {"postings": {"docId": docId}}})
            inverted_index.update_one({"term": term}, {"$push": {"postings": {"docId": docId, "tf": newFrequencies[term]}}})


    # Processing terms that occur only in the new document
    for term, newTf in newFrequencies.items():
        if term not in oldFrequencies: addPosting(term, docId, newTf)


    # Updating the document text
    documents.update_one({"_id": docId}, {"$set": {"text": newText}})



#-------------------------------------------------------------------------
# FUNCTION: deleteDocument
# SPECIFICATION: deletes a document and removes all of its postings from
#                the inverted index
#-------------------------------------------------------------------------
def deleteDocument(docId):

    # Retrieving the document before deleting it
    document = documents.find_one({"_id": docId})


    # Obtaining the terms contained in the document
    terms = getTermFrequencies(document["text"])


    # Removing the document from every corresponding posting list
    for term in terms: removePosting(term, docId)


    # Deleting the document
    documents.delete_one({"_id": docId})



#-------------------------------------------------------------------------
# Executing the sequence of operations
#-------------------------------------------------------------------------

# Operation 1: document 1 is obtained
document1 = {
    "_id": 1,
    "text": "Summer rain is common in Florida."
}

insertDocument(document1)


# Operation 2: document 2 is obtained
document2 = {
    "_id": 2,
    "text": "Summer is hot in Arizona."
}

insertDocument(document2)


# Operation 3: document 1 is updated
updateDocument(
    1,
    "Summer rain is hot rain in Florida."
)


# Operation 4: document 3 is obtained
document3 = {
    "_id": 3,
    "text": "Hot summer rain in California."
}

insertDocument(document3)


# Operation 5: document 2 is deleted
deleteDocument(2)

# Operation 6: print the content of the documents and inverted_index collections
print("documents:")
for document in documents.find().sort("_id", 1): print(document)

print("\ninverted_index:")
for termDocument in inverted_index.find({}, {"_id": 0}).sort("term", 1): print(termDocument)