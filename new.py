from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email
        }


with app.app_context():
    db.create_all()


@app.route("/users", methods=['POST'])
def create_user():
    data = request.get_json()

    # Jika input berupa list: Tambah banyak user sekaligus
    if isinstance(data, list):
        users_created = []

        for item in data:
            if 'username' not in item or 'email' not in item:
                continue

            if User.query.filter_by(username=item['username']).first() or \
               User.query.filter_by(email=item['email']).first():
                continue

            new_user = User(username=item['username'], email=item['email'])
            db.session.add(new_user)
            users_created.append(new_user)

        db.session.commit()

        return jsonify([u.to_dict() for u in users_created]), 201

    # Jika input hanya satu user
    if 'username' not in data or 'email' not in data:
        return jsonify({"error": "Data tidak lengkap"}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username sudah dipakai"}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email sudah dipakai"}), 400

    new_user = User(username=data['username'], email=data['email'])
    db.session.add(new_user)
    db.session.commit()

    return jsonify(new_user.to_dict()), 201


# --- 2. READ (All): Melihat Semua User ---
@app.route("/users", methods=['GET'])
def get_all_users():
    # Ambil semua data dari tabel User
    semua_user_obj = User.query.all()

    # Ubah list objek [User, User, User] menjadi list dictionary
    semua_user_dict = []
    for user in semua_user_obj:
        semua_user_dict.append(user.to_dict())

    return jsonify(semua_user_dict)


# --- 3. READ (Detail): Melihat Satu User Spesifik ---
@app.route("/users/<int:user_id>", methods=['GET'])
def get_user_by_id(user_id):

    user = db.get_or_404(User, user_id, description="User tidak ditemukan")

    return jsonify(user.to_dict())


# --- 4. UPDATE: Memperbarui Data User ---
@app.route("/users/<int:user_id>", methods=['PUT'])
def update_user_by_id(user_id):
    user = db.get_or_404(User, user_id, description="User tidak ditemukan")
    data_update = request.json

    # Update data user
    if 'username' in data_update:
        user.username = data_update['username']
    if 'email' in data_update:
        user.email = data_update['email']

    # Simpan perubahan
    try:
        db.session.commit()
        return jsonify(user.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Gagal update, username/email mungkin sudah dipakai"}), 400


# --- 5. DELETE: Menghapus User ---
@app.route("/users/<int:user_id>", methods=['DELETE'])
def delete_user_by_id(user_id):
    user = db.get_or_404(User, user_id, description="User tidak ditemukan")

    # Hapus dari database
    db.session.delete(user)
    db.session.commit()

    return jsonify({"status": "sukses", "pesan": f"User {user.username} (ID: {user_id}) telah dihapus."})


# --- Menjalankan server ---
if __name__ == '__main__':
    app.run(debug=True)
