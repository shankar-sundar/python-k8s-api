from flask import Flask, jsonify, request

app = Flask(__name__)

# Sample data
books = [
    {
        'id': 1,
        'title': 'Book 1',
        'author': 'Author 1',
    },
    {
        'id': 2,
        'title': 'Book 2',
        'author': 'Author 2',
    },
]

# GET /books - Retrieve all books
@app.route('/books', methods=['GET'])
def get_books():
    return jsonify(books)

# GET /books/<int:id> - Retrieve a specific book
@app.route('/books/<int:id>', methods=['GET'])
def get_book(id):
    book = next((book for book in books if book['id'] == id), None)
    if book:
        return jsonify(book)
    else:
        return jsonify({'message': 'Book not found'}), 404

# POST /books - Create a new book
@app.route('/books', methods=['POST'])
def create_book():
    new_book = {
        'id': request.json['id'],
        'title': request.json['title'],
        'author': request.json['author'],
    }
    books.append(new_book)
    return jsonify(new_book), 201

# PUT /books/<int:id> - Update an existing book
@app.route('/books/<int:id>', methods=['PUT'])
def update_book(id):
    book = next((book for book in books if book['id'] == id), None)
    if book:
        book['title'] = request.json['title']
        book['author'] = request.json['author']
        return jsonify(book)
    else:
        return jsonify({'message': 'Book not found'}), 404

# DELETE /books/<int:id> - Delete a book
@app.route('/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    book = next((book for book in books if book['id'] == id), None)
    if book:
        books.remove(book)
        return jsonify({'message': 'Book deleted'})
    else:
        return jsonify({'message': 'Book not found'}), 404

if __name__ == '__main__':
    app.run()
