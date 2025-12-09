
import customtkinter as ctk
from tkinter import ttk, messagebox, simpledialog
from datetime import date, timedelta
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Database Connection Class
class Database:
    def __init__(self):
        try:
            # Connect to PostgreSQL server to create database if not exists
            conn = psycopg2.connect(
                dbname="smart_library_db",
                user="postgres",
                password="borntokillb2k,",  # Replace with your actual PostgreSQL password
                host="localhost"
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'smart_library_db'")
            exists = cur.fetchone()
            if not exists:
                cur.execute("CREATE DATABASE smart_library_db")
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error creating database: {e}")

        # Now connect to the smartlibrary_db
        self.conn = psycopg2.connect(
            dbname="smart_library_db",
            user="postgres",
            password="borntokillb2k,",  # Replace with your actual PostgreSQL password
            host="localhost"
        )

    def execute(self, query, params=None):
        cur = self.conn.cursor()
        try:
            cur.execute(query, params)
            self.conn.commit()
            if cur.description:
                return cur.fetchall()
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            cur.close()

    def execute_many(self, query, params_list):
        cur = self.conn.cursor()
        try:
            cur.executemany(query, params_list)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            cur.close()

    def fetchone(self, query, params=None):
        cur = self.conn.cursor()
        try:
            cur.execute(query, params)
            return cur.fetchone()
        finally:
            cur.close()

    def close(self):
        self.conn.close()

# Entity Classes
class Role:
    def __init__(self, role_id, name):
        self._id = role_id
        self._name = name

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

class User:
    def __init__(self, user_id, username, role_id, name, email):
        self._id = user_id
        self._username = username
        self._role_id = role_id
        self._name = name
        self._email = email

    @property
    def id(self):
        return self._id

    @property
    def username(self):
        return self._username

    @property
    def role_id(self):
        return self._role_id

    @property
    def name(self):
        return self._name

    @property
    def email(self):
        return self._email

class Member(User):
    def __init__(self, member_id, user_id, username, role_id, name, email, student_id, contact):
        super().__init__(user_id, username, role_id, name, email)
        self._member_id = member_id
        self._student_id = student_id
        self._contact = contact

    @property
    def member_id(self):
        return self._member_id

    @property
    def student_id(self):
        return self._student_id

    @property
    def contact(self):
        return self._contact

class Librarian(User):
    def __init__(self, user_id, username, role_id, name, email):
        super().__init__(user_id, username, role_id, name, email)

class Author:
    def __init__(self, author_id, name, bio):
        self._id = author_id
        self._name = name
        self._bio = bio

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def bio(self):
        return self._bio

class Book:
    def __init__(self, book_id, title, isbn, genre, available, author_id):
        self._id = book_id
        self._title = title
        self._isbn = isbn
        self._genre = genre
        self._available = available
        self._author_id = author_id

    @property
    def id(self):
        return self._id

    @property
    def title(self):
        return self._title

    @property
    def isbn(self):
        return self._isbn

    @property
    def genre(self):
        return self._genre

    @property
    def available(self):
        return self._available

    @property
    def author_id(self):
        return self._author_id

class Loan:
    def __init__(self, loan_id, book_id, member_id, borrow_date, due_date, return_date, status):
        self._id = loan_id
        self._book_id = book_id
        self._member_id = member_id
        self._borrow_date = borrow_date
        self._due_date = due_date
        self._return_date = return_date
        self._status = status

    @property
    def id(self):
        return self._id

    @property
    def book_id(self):
        return self._book_id

    @property
    def member_id(self):
        return self._member_id

    @property
    def borrow_date(self):
        return self._borrow_date

    @property
    def due_date(self):
        return self._due_date

    @property
    def return_date(self):
        return self._return_date

    @property
    def status(self):
        return self._status

class BookClub:
    def __init__(self, club_id, name, description, created_by):
        self._id = club_id
        self._name = name
        self._description = description
        self._created_by = created_by

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def created_by(self):
        return self._created_by

# DAO Classes
class RoleDAO:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        rows = self.db.execute("SELECT id, name FROM roles")
        return [Role(r[0], r[1]) for r in rows]

class UserDAO:
    def __init__(self, db):
        self.db = db

    def authenticate(self, username, password):
        row = self.db.fetchone("""
            SELECT u.id, u.username, u.role_id, u.name, u.email, r.name as role_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.username = %s AND u.password_hash = crypt(%s, u.password_hash)
        """, (username, password))
        if row:
            if row[5] == 'Member':
                member_row = self.db.fetchone("""
                    SELECT m.id, m.student_id, m.contact
                    FROM members m WHERE m.user_id = %s
                """, (row[0],))
                if member_row:
                    return Member(member_row[0], row[0], row[1], row[2], row[3], row[4], member_row[1], member_row[2])
            elif row[5] == 'Librarian':
                return Librarian(row[0], row[1], row[2], row[3], row[4])
        return None

    def get_member_id_by_email(self, email):
        row = self.db.fetchone("""
            SELECT m.id FROM members m JOIN users u ON m.user_id = u.id WHERE u.email = %s
        """, (email,))
        return row[0] if row else None

    def get_all_members(self):
        rows = self.db.execute("""
            SELECT m.id, u.id, u.username, u.role_id, u.name, u.email, m.student_id, m.contact
            FROM members m JOIN users u ON m.user_id = u.id
        """)
        return [Member(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]) for r in rows]

    def create_member(self, username, password, name, email, student_id, contact):
        role_id = self.db.fetchone("SELECT id FROM roles WHERE name = 'Member'")[0]
        self.db.execute("""
            INSERT INTO users (username, password_hash, role_id, name, email)
            VALUES (%s, crypt(%s, gen_salt('bf')), %s, %s, %s)
        """, (username, password, role_id, name, email))
        user_id = self.db.fetchone("SELECT id FROM users WHERE username = %s", (username,))[0]
        self.db.execute("""
            INSERT INTO members (user_id, student_id, contact)
            VALUES (%s, %s, %s)
        """, (user_id, student_id, contact))

    def update_member(self, member_id, username, name, email, student_id, contact):
        user_id = self.db.fetchone("SELECT user_id FROM members WHERE id = %s", (member_id,))[0]
        self.db.execute("""
            UPDATE users SET username = %s, name = %s, email = %s WHERE id = %s
        """, (username, name, email, user_id))
        self.db.execute("""
            UPDATE members SET student_id = %s, contact = %s WHERE id = %s
        """, (student_id, contact, member_id))

    def delete_member(self, member_id):
        user_id = self.db.fetchone("SELECT user_id FROM members WHERE id = %s", (member_id,))[0]
        self.db.execute("DELETE FROM members WHERE id = %s", (member_id,))
        self.db.execute("DELETE FROM users WHERE id = %s", (user_id,))

class AuthorDAO:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        rows = self.db.execute("SELECT id, name, bio FROM authors")
        return [Author(r[0], r[1], r[2]) for r in rows]

    def create(self, name, bio):
        self.db.execute("INSERT INTO authors (name, bio) VALUES (%s, %s)", (name, bio))

    def update(self, author_id, name, bio):
        self.db.execute("UPDATE authors SET name = %s, bio = %s WHERE id = %s", (name, bio, author_id))

    def delete(self, author_id):
        self.db.execute("DELETE FROM authors WHERE id = %s", (author_id,))

    def search(self, query):
        rows = self.db.execute("SELECT id, name, bio FROM authors WHERE name ILIKE %s", (f"%{query}%",))
        return [Author(r[0], r[1], r[2]) for r in rows]

class BookDAO:
    def __init__(self, db):
        self.db = db

    def get_book_id_by_isbn(self, isbn):
        row = self.db.fetchone("SELECT id FROM books WHERE isbn = %s AND available = TRUE", (isbn,))
        return row[0] if row else None

    def get_all(self):
        rows = self.db.execute("SELECT id, title, isbn, genre, available, author_id FROM books")
        return [Book(r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows]

    def create(self, title, isbn, genre, author_id):
        self.db.execute("""
            INSERT INTO books (title, isbn, genre, author_id)
            VALUES (%s, %s, %s, %s)
        """, (title, isbn, genre, author_id))

    def update(self, book_id, title, isbn, genre, author_id, available):
        self.db.execute("""
            UPDATE books SET title = %s, isbn = %s, genre = %s, author_id = %s, available = %s
            WHERE id = %s
        """, (title, isbn, genre, author_id, available, book_id))

    def delete(self, book_id):
        self.db.execute("DELETE FROM books WHERE id = %s", (book_id,))

    def search(self, query):
        rows = self.db.execute("""
            SELECT b.id, b.title, b.isbn, b.genre, b.available, b.author_id
            FROM books b JOIN authors a ON b.author_id = a.id
            WHERE b.title ILIKE %s OR a.name ILIKE %s OR b.genre ILIKE %s
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        return [Book(r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows]

class LoanDAO:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        rows = self.db.execute("""
            SELECT id, book_id, member_id, borrow_date, due_date, return_date, status
            FROM loans
        """)
        return [Loan(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) for r in rows]

    def get_by_member(self, member_id):
        rows = self.db.execute("""
            SELECT id, book_id, member_id, borrow_date, due_date, return_date, status
            FROM loans WHERE member_id = %s
        """, (member_id,))
        return [Loan(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) for r in rows]

    def create(self, book_id, member_id):
        self.db.execute("""
            INSERT INTO loans (book_id, member_id)
            VALUES (%s, %s)
        """, (book_id, member_id))
        self.db.execute("UPDATE books SET available = FALSE WHERE id = %s", (book_id,))

    def return_book(self, loan_id):
        self.db.execute("""
            UPDATE loans SET return_date = CURRENT_DATE, status = 'Returned'
            WHERE id = %s
        """, (loan_id,))
        book_id = self.db.fetchone("SELECT book_id FROM loans WHERE id = %s", (loan_id,))[0]
        self.db.execute("UPDATE books SET available = TRUE WHERE id = %s", (book_id,))

    def update_overdue(self):
        self.db.execute("SELECT update_overdue_loans()")

class BookClubDAO:
    def __init__(self, db):
        self.db = db

    def get_all(self):
        rows = self.db.execute("""
            SELECT id, name, description, created_by FROM book_clubs
        """)
        return [BookClub(r[0], r[1], r[2], r[3]) for r in rows]

    def create(self, name, description, created_by):
        self.db.execute("""
            INSERT INTO book_clubs (name, description, created_by)
            VALUES (%s, %s, %s)
        """, (name, description, created_by))

    def update(self, club_id, name, description):
        self.db.execute("""
            UPDATE book_clubs SET name = %s, description = %s WHERE id = %s
        """, (name, description, club_id))

    def delete(self, club_id):
        self.db.execute("DELETE FROM book_clubs WHERE id = %s", (club_id,))

    def get_members(self, club_id):
        rows = self.db.execute("""
            SELECT m.id FROM book_club_members bcm
            JOIN members m ON bcm.member_id = m.id
            WHERE bcm.club_id = %s
        """, (club_id,))
        return [r[0] for r in rows]

    def add_member(self, club_id, member_id):
        self.db.execute("""
            INSERT INTO book_club_members (club_id, member_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (club_id, member_id))

    def remove_member(self, club_id, member_id):
        self.db.execute("""
            DELETE FROM book_club_members WHERE club_id = %s AND member_id = %s
        """, (club_id, member_id))

# Main App
class SmartLibraryApp(ctk.CTk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.title("SmartLibrary - Limkokwing University")
        self.geometry("1500x900")

        self.user = None
        self.show_login_screen()

    def show_login_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

        main_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        main_frame.pack(fill="both", expand=True)

        center = ctk.CTkFrame(main_frame, width=520, height=650, corner_radius=30, fg_color="#2d2d2d")
        center.place(relx=0.5, rely=0.5, anchor="center")
        center.pack_propagate(False)

        ctk.CTkLabel(center, text="SmartLibrary", font=ctk.CTkFont(size=60, weight="bold"), text_color="#00d4ff").pack(pady=(70,10))
        ctk.CTkLabel(center, text="Limkokwing University", font=ctk.CTkFont(size=22), text_color="gray").pack(pady=(0,60))

        self.username_entry = ctk.CTkEntry(center, placeholder_text="Username", width=400, height=55, font=ctk.CTkFont(size=16))
        self.username_entry.pack(pady=15)
        self.pass_entry = ctk.CTkEntry(center, placeholder_text="Password", width=400, height=55, show="*", font=ctk.CTkFont(size=16))
        self.pass_entry.pack(pady=15)

        ctk.CTkButton(center, text="LOGIN", width=400, height=65, corner_radius=20,
                     font=ctk.CTkFont(size=22, weight="bold"), fg_color="#00d4ff",
                     command=self.perform_login).pack(pady=40)

        ctk.CTkLabel(center, text="Demo Accounts (Password: password123)\n"
                                 "Librarians: admin, librarian1\n"
                                 "Members: john_doe, jane_smith, mike_brown, emma_wilson, david_lee",
                     text_color="#888888", font=ctk.CTkFont(size=14)).pack(pady=20)

    def perform_login(self):
        username = self.username_entry.get().strip()
        password = self.pass_entry.get()
        user_dao = UserDAO(self.db)
        user = user_dao.authenticate(username, password)
        if user:
            self.user = user
            self.build_main_interface()
            messagebox.showinfo("Success", f"Welcome, {self.user.name}!")
        else:
            messagebox.showerror("Login Failed", "Invalid username or password!")

    def build_main_interface(self):
        for widget in self.winfo_children():
            widget.destroy()

        sidebar = ctk.CTkFrame(self, width=300, corner_radius=0, fg_color="#212121")
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="SmartLibrary", font=ctk.CTkFont(size=28, weight="bold"), text_color="#00d4ff").pack(pady=40)
        ctk.CTkLabel(sidebar, text=f"{self.user.name}\n{'Librarian' if isinstance(self.user, Librarian) else 'Member'}",
                     text_color="#00ff88", font=ctk.CTkFont(size=16)).pack(pady=20)

        menu = [
            ("Dashboard", self.show_dashboard),
            ("Book Catalog", self.show_book_catalog),
        ]

        if isinstance(self.user, Member):
            menu += [
                ("My Loans", self.show_my_loans),
                ("Book Clubs", self.show_book_clubs_member),
            ]

        if isinstance(self.user, Librarian):
            menu += [
                ("Issue Book", self.show_issue_book),
                ("Return Book", self.show_return_book),
                ("Manage Books", self.show_manage_books),
                ("Manage Authors", self.show_manage_authors),
                ("Manage Members", self.show_manage_members),
                ("Manage Loans", self.show_manage_loans),
                ("Manage Book Clubs", self.show_manage_book_clubs),
            ]

        for text, cmd in menu:
            btn = ctk.CTkButton(sidebar, text=text, command=cmd, height=55, fg_color="transparent",
                                hover_color="#333333", anchor="w", font=ctk.CTkFont(size=16))
            btn.pack(pady=8, padx=25, fill="x")

        self.content_area = ctk.CTkFrame(self, fg_color="#1e1e1e")
        self.content_area.pack(fill="both", expand=True, padx=20, pady=20)

        logout_btn = ctk.CTkButton(
            self,
            text="LOGOUT",
            width=160,
            height=50,
            corner_radius=25,
            fg_color="#ff3333",
            hover_color="#ff0000",
            text_color="white",
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.show_login_screen
        )
        logout_btn.place(relx=0.97, rely=0.035, anchor="ne")

        user_label = ctk.CTkLabel(
            self,
            text=f"{self.user.name}",
            text_color="#00ff88",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        user_label.place(relx=0.97, rely=0.095, anchor="ne")

        self.show_dashboard()

    def show_dashboard(self):
        for w in self.content_area.winfo_children():
            w.destroy()

        top_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        top_frame.pack(fill="x", pady=(30, 20), padx=60)

        ctk.CTkLabel(top_frame, text=date.today().strftime("%A, %B %d, %Y"),
                     font=ctk.CTkFont(size=18), text_color="#aaaaaa").pack(side="left")

        welcome = ctk.CTkFrame(top_frame, fg_color="transparent")
        welcome.pack(expand=True)
        ctk.CTkLabel(welcome, text="Welcome back,", font=ctk.CTkFont(size=28), text_color="#cccccc").pack(side="left")
        ctk.CTkLabel(welcome, text=self.user.name, font=ctk.CTkFont(size=36, weight="bold"),
                     text_color="#00ff88").pack(side="left", padx=(5, 10))
        ctk.CTkLabel(welcome, text=f"• {'Librarian' if isinstance(self.user, Librarian) else 'Member'}", font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="#00d4ff").pack(side="left")

        ctk.CTkLabel(self.content_area, text="Dashboard Overview",
                     font=ctk.CTkFont(size=48, weight="bold"), text_color="white").pack(pady=(10, 60))

        book_dao = BookDAO(self.db)
        loan_dao = LoanDAO(self.db)
        loan_dao.update_overdue()
        total_books = len(book_dao.get_all())
        available_books = sum(1 for b in book_dao.get_all() if b.available)
        borrowed_books = sum(1 for l in loan_dao.get_all() if l.status in ('Active', 'Overdue'))
        overdue_loans = sum(1 for l in loan_dao.get_all() if l.status == 'Overdue')

        stats_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        stats_frame.pack(fill="both", expand=True, padx=100, pady=(0, 100))

        cards = [
            ("Total Books", total_books, "#6366f1"),
            ("Available Books", available_books, "#10b981"),
            ("Borrowed Books", borrowed_books, "#f59e0b"),
            ("Overdue Loans", overdue_loans, "#ef4444"),
        ]

        for i, (title, value, color) in enumerate(cards):
            card = ctk.CTkFrame(stats_frame, corner_radius=28, fg_color=color, height=220)
            card.grid(row=0, column=i, padx=28, pady=30, sticky="nsew")
            card.grid_propagate(False)

            ctk.CTkLabel(card, text=str(value),
                         font=ctk.CTkFont(size=72, weight="bold"), text_color="white").pack(pady=(45, 8))
            ctk.CTkLabel(card, text=title,
                         font=ctk.CTkFont(size=22, weight="bold"), text_color="white").pack()

        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)
        stats_frame.grid_rowconfigure(0, weight=1)

    def show_book_catalog(self):
        for w in self.content_area.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.content_area, text="Book Catalog", font=ctk.CTkFont(size=44, weight="bold")).pack(pady=30)

        search_bar = ctk.CTkFrame(self.content_area)
        search_bar.pack(pady=20, fill="x", padx=100)

        self.search_entry = ctk.CTkEntry(
            search_bar,
            placeholder_text="Search by title, author, or genre...",
            width=600,
            height=50,
            font=ctk.CTkFont(size=16)
        )
        self.search_entry.pack(side="left", padx=10)
        self.search_entry.focus()

        search_btn = ctk.CTkButton(
            search_bar,
            text="SEARCH",
            width=150,
            height=50,
            fg_color="#00d4ff",
            command=self.perform_search_books
        )
        search_btn.pack(side="left", padx=10)

        self.search_entry.bind("<Return>", lambda event: self.perform_search_books())

        style = ttk.Style()
        style.configure("Treeview", font=('Helvetica', 12), rowheight=40)
        style.configure("Treeview.Heading", font=('Helvetica', 14, 'bold'))

        self.book_tree = ttk.Treeview(
            self.content_area,
            columns=("ID", "Title", "ISBN", "Genre", "Available"),
            show="headings",
            height=22
        )
        for col in self.book_tree["columns"]:
            self.book_tree.heading(col, text=col)
            self.book_tree.column(col, width=180, anchor="center")
        self.book_tree.pack(pady=20, fill="both", expand=True, padx=50)

        self.book_tree.bind("<<TreeviewSelect>>", self.on_book_select)

        self.book_action_frame = ctk.CTkFrame(self.content_area)
        self.book_action_frame.pack(pady=10)

        self.perform_search_books()

    def perform_search_books(self):
        query = self.search_entry.get()
        book_dao = BookDAO(self.db)
        books = book_dao.search(query) if query else book_dao.get_all()

        for item in self.book_tree.get_children():
            self.book_tree.delete(item)

        for book in books:
            self.book_tree.insert("", "end", values=(
                book.id,
                book.title,
                book.isbn,
                book.genre,
                "Yes" if book.available else "No"
            ))

        if not books and query:
            self.book_tree.insert("", "end", values=("", "No books found...", "", "", ""))

    def on_book_select(self, event):
        for w in self.book_action_frame.winfo_children():
            w.destroy()

        selected = event.widget.focus()
        if selected:
            values = event.widget.item(selected, "values")
            if isinstance(self.user, Member) and values[4] == "Yes":
                loan_btn = ctk.CTkButton(self.book_action_frame, text="Loan this Book", fg_color="#10b981",
                                         command=lambda: self.loan_selected_book(values[0]))
                loan_btn.pack()

    def loan_selected_book(self, book_id):
        try:
            loan_dao = LoanDAO(self.db)
            loan_dao.create(int(book_id), self.user.member_id)
            messagebox.showinfo("Success", "Book loaned successfully!")
            self.perform_search_books()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_my_loans(self):
        for w in self.content_area.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.content_area, text="My Loans", font=ctk.CTkFont(size=44, weight="bold")).pack(pady=40)

        loan_dao = LoanDAO(self.db)
        book_dao = BookDAO(self.db)
        loans = loan_dao.get_by_member(self.user.member_id)
        books = {b.id: b.title for b in book_dao.get_all()}

        style = ttk.Style()
        style.configure("Treeview", font=('Helvetica', 12), rowheight=40)
        style.configure("Treeview.Heading", font=('Helvetica', 14, 'bold'))

        self.my_loans_tree = ttk.Treeview(self.content_area, columns=("ID", "Book Title", "Borrow Date", "Due Date", "Return Date", "Status"), show="headings", height=15)
        for col in self.my_loans_tree["columns"]:
            self.my_loans_tree.heading(col, text=col)
            self.my_loans_tree.column(col, width=200, anchor="center")
        self.my_loans_tree.pack(pady=20, fill="both", expand=True, padx=50)

        for loan in loans:
            self.my_loans_tree.insert("", "end", values=(
                loan.id,
                books.get(loan.book_id, "Unknown"),
                loan.borrow_date.strftime("%Y-%m-%d"),
                loan.due_date.strftime("%Y-%m-%d"),
                loan.return_date.strftime("%Y-%m-%d") if loan.return_date else "N/A",
                loan.status
            ))

        self.my_loans_tree.bind("<<TreeviewSelect>>", self.on_my_loan_select)

        self.my_loan_action_frame = ctk.CTkFrame(self.content_area)
        self.my_loan_action_frame.pack(pady=10)

        if not loans:
            ctk.CTkLabel(self.content_area, text="No loans.", text_color="gray").pack(pady=20)

    def on_my_loan_select(self, event):
        for w in self.my_loan_action_frame.winfo_children():
            w.destroy()

        selected = event.widget.focus()
        if selected:
            values = event.widget.item(selected, "values")
            if values[5] in ('Active', 'Overdue'):
                return_btn = ctk.CTkButton(self.my_loan_action_frame, text="Return Book", fg_color="#ef4444",
                                           command=lambda: self.return_selected_loan(values[0]))
                return_btn.pack()

    def return_selected_loan(self, loan_id):
        try:
            loan_dao = LoanDAO(self.db)
            loan_dao.return_book(int(loan_id))
            messagebox.showinfo("Success", "Book returned successfully!")
            self.show_my_loans()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_book_clubs_member(self):
        for w in self.content_area.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.content_area, text="Book Clubs", font=ctk.CTkFont(size=44, weight="bold")).pack(pady=40)

        book_club_dao = BookClubDAO(self.db)
        clubs = book_club_dao.get_all()

        style = ttk.Style()
        style.configure("Treeview", font=('Helvetica', 12), rowheight=40)
        style.configure("Treeview.Heading", font=('Helvetica', 14, 'bold'))

        self.clubs_tree = ttk.Treeview(self.content_area, columns=("ID", "Name", "Description"), show="headings", height=15)
        for col in self.clubs_tree["columns"]:
            self.clubs_tree.heading(col, text=col)
            self.clubs_tree.column(col, width=300, anchor="center")
        self.clubs_tree.pack(pady=20, fill="both", expand=True, padx=50)

        for club in clubs:
            self.clubs_tree.insert("", "end", values=(club.id, club.name, club.description))

        self.clubs_tree.bind("<<TreeviewSelect>>", self.on_club_select_member)

        self.club_action_frame = ctk.CTkFrame(self.content_area)
        self.club_action_frame.pack(pady=10)

    def on_club_select_member(self, event):
        for w in self.club_action_frame.winfo_children():
            w.destroy()

        selected = event.widget.focus()
        if selected:
            values = event.widget.item(selected, "values")
            club_id = int(values[0])
            book_club_dao = BookClubDAO(self.db)
            is_member = self.user.member_id in book_club_dao.get_members(club_id)
            if is_member:
                leave_btn = ctk.CTkButton(self.club_action_frame, text="Leave Club", fg_color="#ef4444",
                                          command=lambda: self.leave_club(club_id))
                leave_btn.pack()
            else:
                join_btn = ctk.CTkButton(self.club_action_frame, text="Join Club", fg_color="#10b981",
                                         command=lambda: self.join_club(club_id))
                join_btn.pack()

    def join_club(self, club_id):
        book_club_dao = BookClubDAO(self.db)
        book_club_dao.add_member(club_id, self.user.member_id)
        messagebox.showinfo("Success", "Joined club successfully!")
        self.show_book_clubs_member()

    def leave_club(self, club_id):
        book_club_dao = BookClubDAO(self.db)
        book_club_dao.remove_member(club_id, self.user.member_id)
        messagebox.showinfo("Success", "Left club successfully!")
        self.show_book_clubs_member()

    def show_issue_book(self):
        for w in self.content_area.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.content_area, text="Issue Book", font=ctk.CTkFont(size=44, weight="bold")).pack(pady=40)

        form = ctk.CTkFrame(self.content_area)
        form.pack(pady=30, padx=200, fill="x")

        ctk.CTkLabel(form, text="Member Email:").grid(row=0, column=0, pady=15, padx=10, sticky="e")
        self.member_email_entry = ctk.CTkEntry(form, width=400)
        self.member_email_entry.grid(row=0, column=1, pady=15, padx=10)

        ctk.CTkLabel(form, text="Book ISBN:").grid(row=1, column=0, pady=15, padx=10, sticky="e")
        self.isbn_entry = ctk.CTkEntry(form, width=400)
        self.isbn_entry.grid(row=1, column=1, pady=15, padx=10)

        ctk.CTkLabel(form, text="Due Days:").grid(row=2, column=0, pady=15, padx=10, sticky="e")
        self.due_days_entry = ctk.CTkEntry(form, placeholder_text="7", width=400)
        self.due_days_entry.grid(row=2, column=1, pady=15, padx=10)

        ctk.CTkButton(form, text="ISSUE BOOK", fg_color="#10b981", command=self.perform_issue_book).grid(row=3, column=0, columnspan=2, pady=30)

    def perform_issue_book(self):
        member_email = self.member_email_entry.get().strip()
        isbn = self.isbn_entry.get().strip()
        due_days = int(self.due_days_entry.get() or 7)
        if not member_email or not isbn:
            messagebox.showerror("Error", "Member email and ISBN required!")
            return

        user_dao = UserDAO(self.db)
        member_id = user_dao.get_member_id_by_email(member_email)
        if not member_id:
            messagebox.showerror("Error", "Member not found!")
            return

        loan_dao = LoanDAO(self.db)
        active_loans = len([l for l in loan_dao.get_by_member(member_id) if l.status == 'Active'])
        if active_loans >= 3:
            messagebox.showerror("Error", "Member has reached max loans!")
            return

        book_dao = BookDAO(self.db)
        book_id = book_dao.get_book_id_by_isbn(isbn)
        if not book_id:
            messagebox.showerror("Error", "Book not found or unavailable!")
            return

        loan_dao.create(book_id, member_id)
        messagebox.showinfo("Success", f"Book issued! Due in {due_days} days.")

    def show_return_book(self):
        for w in self.content_area.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.content_area, text="Return Book", font=ctk.CTkFont(size=44, weight="bold")).pack(pady=40)

        form = ctk.CTkFrame(self.content_area)
        form.pack(pady=30, padx=200, fill="x")

        ctk.CTkLabel(form, text="Loan ID:").grid(row=0, column=0, pady=15, padx=10, sticky="e")
        self.loan_id_entry = ctk.CTkEntry(form, width=400)
        self.loan_id_entry.grid(row=0, column=1, pady=15, padx=10)

        ctk.CTkButton(form, text="RETURN BOOK", fg_color="#ef4444", command=self.perform_return_book).grid(row=1, column=0, columnspan=2, pady=30)

    def perform_return_book(self):
        loan_id = self.loan_id_entry.get().strip()
        if not loan_id:
            messagebox.showerror("Error", "Loan ID required!")
            return

        loan_dao = LoanDAO(self.db)
        loan = next((l for l in loan_dao.get_all() if str(l.id) == loan_id and l.status in ('Active', 'Overdue')), None)
        if not loan:
            messagebox.showerror("Error", "Invalid Loan ID or already returned!")
            return

        loan_dao.return_book(int(loan_id))
        messagebox.showinfo("Success", "Book returned successfully!")

    def show_manage_books(self):
        for w in self.content_area.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.content_area, text="Manage Books", font=ctk.CTkFont(size=44, weight="bold")).pack(pady=30)

        form = ctk.CTkFrame(self.content_area)
        form.pack(pady=20, fill="x", padx=100)

        labels = ["Title", "ISBN", "Genre", "Author ID"]
        self.book_entries = {}
        for i, label in enumerate(labels):
            ctk.CTkLabel(form, text=label + ":", font=ctk.CTkFont(size=16)).grid(row=i, column=0, pady=10, padx=10, sticky="e")
            self.book_entries[label] = ctk.CTkEntry(form, width=400, height=40)
            self.book_entries[label].grid(row=i, column=1, pady=10, padx=10)

        add_btn = ctk.CTkButton(form, text="Add Book", fg_color="#10b981", command=self.add_book_ctk)
        add_btn.grid(row=len(labels), column=0, columnspan=2, pady=20)

        style = ttk.Style()
        style.configure("Treeview", font=('Helvetica', 12), rowheight=40)
        style.configure("Treeview.Heading", font=('Helvetica', 14, 'bold'))

        self.manage_book_tree = ttk.Treeview(
            self.content_area,
            columns=("ID", "Title", "ISBN", "Genre", "Available"),
            show="headings",
            height=15
        )
        for col in self.manage_book_tree["columns"]:
            self.manage_book_tree.heading(col, text=col)
            self.manage_book_tree.column(col, width=200, anchor="center")
        self.manage_book_tree.pack(pady=20, fill="both", expand=True, padx=50)

        self.manage_book_tree.bind("<<TreeviewSelect>>", self.on_manage_book_select)

        self.manage_book_action_frame = ctk.CTkFrame(self.content_area)
        self.manage_book_action_frame.pack(pady=10)

        self.refresh_manage_books_tree()

    def add_book_ctk(self):
        title = self.book_entries["Title"].get()
        isbn = self.book_entries["ISBN"].get()
        genre = self.book_entries["Genre"].get()
        author_id = self.book_entries["Author ID"].get()
        if title and isbn and genre and author_id:
            try:
                book_dao = BookDAO(self.db)
                book_dao.create(title, isbn, genre, int(author_id))
                messagebox.showinfo("Success", "Book added!")
                self.refresh_manage_books_tree()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showerror("Error", "All fields required!")

    def refresh_manage_books_tree(self):
        book_dao = BookDAO(self.db)
        books = book_dao.get_all()
        for item in self.manage_book_tree.get_children():
            self.manage_book_tree.delete(item)
        for book in books:
            self.manage_book_tree.insert("", "end", values=(
                book.id,
                book.title,
                book.isbn,
                book.genre,
                "Yes" if book.available else "No"
            ))

    def on_manage_book_select(self, event):
        for w in self.manage_book_action_frame.winfo_children():
            w.destroy()

        selected = event.widget.focus()
        if selected:
            values = event.widget.item(selected, "values")
            edit_btn = ctk.CTkButton(self.manage_book_action_frame, text="Edit", fg_color="#f59e0b",
                                     command=lambda: self.edit_book_ctk(values))
            edit_btn.pack(side="left", padx=10)
            delete_btn = ctk.CTkButton(self.manage_book_action_frame, text="Delete", fg_color="#ef4444",
                                       command=lambda: self.delete_book_ctk(values[0]))
            delete_btn.pack(side="left", padx=10)

    def edit_book_ctk(self, values):
        title = simpledialog.askstring("Edit Title", "Title:", initialvalue=values[1])
        if title is None: return
        isbn = simpledialog.askstring("Edit ISBN", "ISBN:", initialvalue=values[2])
        if isbn is None: return
        genre = simpledialog.askstring("Edit Genre", "Genre:", initialvalue=values[3])
        if genre is None: return
        author_id = simpledialog.askinteger("Edit Author ID", "Author ID:")
        if author_id is None: return
        available = values[4] == "Yes"
        book_dao = BookDAO(self.db)
        book_dao.update(int(values[0]), title, isbn, genre, author_id, available)
        messagebox.showinfo("Success", "Book updated!")
        self.refresh_manage_books_tree()

    def delete_book_ctk(self, book_id):
        if messagebox.askyesno("Confirm", "Delete this book?"):
            book_dao = BookDAO(self.db)
            book_dao.delete(int(book_id))
            messagebox.showinfo("Success", "Book deleted!")
            self.refresh_manage_books_tree()

    def show_manage_authors(self):
        for w in self.content_area.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.content_area, text="Manage Authors", font=ctk.CTkFont(size=44, weight="bold")).pack(pady=30)

        form = ctk.CTkFrame(self.content_area)
        form.pack(pady=20, fill="x", padx=100)

        labels = ["Name", "Bio"]
        self.author_entries = {}
        for i, label in enumerate(labels):
            ctk.CTkLabel(form, text=label + ":", font=ctk.CTkFont(size=16)).grid(row=i, column=0, pady=10, padx=10, sticky="e")
            if label == "Bio":
                self.author_entries[label] = ctk.CTkTextbox(form, width=400, height=100)
            else:
                self.author_entries[label] = ctk.CTkEntry(form, width=400, height=40)
            self.author_entries[label].grid(row=i, column=1, pady=10, padx=10)

        add_btn = ctk.CTkButton(form, text="Add Author", fg_color="#10b981", command=self.add_author_ctk)
        add_btn.grid(row=len(labels), column=0, columnspan=2, pady=20)

        style = ttk.Style()
        style.configure("Treeview", font=('Helvetica', 12), rowheight=40)
        style.configure("Treeview.Heading", font=('Helvetica', 14, 'bold'))

        self.manage_author_tree = ttk.Treeview(
            self.content_area,
            columns=("ID", "Name", "Bio"),
            show="headings",
            height=15
        )
        for col in self.manage_author_tree["columns"]:
            self.manage_author_tree.heading(col, text=col)
            self.manage_author_tree.column(col, width=200, anchor="center")
        self.manage_author_tree.pack(pady=20, fill="both", expand=True, padx=50)

        self.manage_author_tree.bind("<<TreeviewSelect>>", self.on_manage_author_select)

        self.manage_author_action_frame = ctk.CTkFrame(self.content_area)
        self.manage_author_action_frame.pack(pady=10)

        self.refresh_manage_authors_tree()

    def add_author_ctk(self):
        name = self.author_entries["Name"].get()
        bio = self.author_entries["Bio"].get("1.0", "end-1c")
        if name:
            author_dao = AuthorDAO(self.db)
            author_dao.create(name, bio)
            messagebox.showinfo("Success", "Author added!")
            self.refresh_manage_authors_tree()
        else:
            messagebox.showerror("Error", "Name required!")

    def refresh_manage_authors_tree(self):
        author_dao = AuthorDAO(self.db)
        authors = author_dao.get_all()
        for item in self.manage_author_tree.get_children():
            self.manage_author_tree.delete(item)
        for author in authors:
            self.manage_author_tree.insert("", "end", values=(
                author.id,
                author.name,
                author.bio[:50] + "..." if author.bio else ""
            ))

    def on_manage_author_select(self, event):
        for w in self.manage_author_action_frame.winfo_children():
            w.destroy()

        selected = event.widget.focus()
        if selected:
            values = event.widget.item(selected, "values")
            edit_btn = ctk.CTkButton(self.manage_author_action_frame, text="Edit", fg_color="#f59e0b",
                                     command=lambda: self.edit_author_ctk(values))
            edit_btn.pack(side="left", padx=10)
            delete_btn = ctk.CTkButton(self.manage_author_action_frame, text="Delete", fg_color="#ef4444",
                                       command=lambda: self.delete_author_ctk(values[0]))
            delete_btn.pack(side="left", padx=10)

    def edit_author_ctk(self, values):
        name = simpledialog.askstring("Edit Name", "Name:", initialvalue=values[1])
        if name is None: return
        bio = simpledialog.askstring("Edit Bio", "Bio:", initialvalue="")
        if bio is None: return
        author_dao = AuthorDAO(self.db)
        author_dao.update(int(values[0]), name, bio)
        messagebox.showinfo("Success", "Author updated!")
        self.refresh_manage_authors_tree()

    def delete_author_ctk(self, author_id):
        if messagebox.askyesno("Confirm", "Delete this author?"):
            author_dao = AuthorDAO(self.db)
            author_dao.delete(int(author_id))
            messagebox.showinfo("Success", "Author deleted!")
            self.refresh_manage_authors_tree()

    def show_manage_members(self):
        for w in self.content_area.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.content_area, text="Manage Members", font=ctk.CTkFont(size=44, weight="bold")).pack(pady=30)

        form = ctk.CTkFrame(self.content_area)
        form.pack(pady=20, fill="x", padx=100)

        labels = ["Username", "Password", "Full Name", "Email", "Student ID", "Contact"]
        self.member_entries = {}
        for i, label in enumerate(labels):
            ctk.CTkLabel(form, text=label + ":", font=ctk.CTkFont(size=16)).grid(row=i, column=0, pady=10, padx=10, sticky="e")
            self.member_entries[label] = ctk.CTkEntry(form, width=400, height=40)
            if label == "Password":
                self.member_entries[label].configure(show="*")
            self.member_entries[label].grid(row=i, column=1, pady=10, padx=10)

        add_btn = ctk.CTkButton(form, text="Add Member", fg_color="#10b981", command=self.add_member_ctk)
        add_btn.grid(row=len(labels), column=0, columnspan=2, pady=20)

        style = ttk.Style()
        style.configure("Treeview", font=('Helvetica', 12), rowheight=40)
        style.configure("Treeview.Heading", font=('Helvetica', 14, 'bold'))

        scroll_frame = ctk.CTkScrollableFrame(self.content_area, height=400)
        scroll_frame.pack(pady=20, fill="both", expand=True, padx=50)

        self.manage_member_tree = ttk.Treeview(
            scroll_frame,
            columns=("ID", "Username", "Name", "Email", "Student ID", "Contact"),
            show="headings",
            height=15
        )
        for col in self.manage_member_tree["columns"]:
            self.manage_member_tree.heading(col, text=col)
            self.manage_member_tree.column(col, width=150, anchor="center")
        self.manage_member_tree.pack(fill="both", expand=True)

        self.manage_member_tree.bind("<<TreeviewSelect>>", self.on_manage_member_select)

        self.manage_member_action_frame = ctk.CTkFrame(self.content_area)
        self.manage_member_action_frame.pack(pady=10)

        self.refresh_manage_members_tree()

    def add_member_ctk(self):
        username = self.member_entries["Username"].get()
        password = self.member_entries["Password"].get()
        name = self.member_entries["Full Name"].get()
        email = self.member_entries["Email"].get()
        student_id = self.member_entries["Student ID"].get()
        contact = self.member_entries["Contact"].get()
        if username and password and name and email and student_id:
            try:
                user_dao = UserDAO(self.db)
                user_dao.create_member(username, password, name, email, student_id, contact)
                messagebox.showinfo("Success", "Member added!")
                self.refresh_manage_members_tree()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showerror("Error", "Required fields missing!")

    def refresh_manage_members_tree(self):
        user_dao = UserDAO(self.db)
        members = user_dao.get_all_members()
        for item in self.manage_member_tree.get_children():
            self.manage_member_tree.delete(item)
        for member in members:
            self.manage_member_tree.insert("", "end", values=(
                member.member_id,
                member.username,
                member.name,
                member.email,
                member.student_id,
                member.contact or "N/A"
            ))

    def on_manage_member_select(self, event):
        for w in self.manage_member_action_frame.winfo_children():
            w.destroy()

        selected = event.widget.focus()
        if selected:
            values = event.widget.item(selected, "values")
            edit_btn = ctk.CTkButton(self.manage_member_action_frame, text="Edit", fg_color="#f59e0b",
                                     command=lambda: self.edit_member_ctk(values))
            edit_btn.pack(side="left", padx=10)
            delete_btn = ctk.CTkButton(self.manage_member_action_frame, text="Delete", fg_color="#ef4444",
                                       command=lambda: self.delete_member_ctk(values[0]))
            delete_btn.pack(side="left", padx=10)

    def edit_member_ctk(self, values):
        username = simpledialog.askstring("Edit Username", "Username:", initialvalue=values[1])
        if username is None: return
        name = simpledialog.askstring("Edit Name", "Full Name:", initialvalue=values[2])
        if name is None: return
        email = simpledialog.askstring("Edit Email", "Email:", initialvalue=values[3])
        if email is None: return
        student_id = simpledialog.askstring("Edit Student ID", "Student ID:", initialvalue=values[4])
        if student_id is None: return
        contact = simpledialog.askstring("Edit Contact", "Contact:", initialvalue=values[5])
        if contact is None: return
        user_dao = UserDAO(self.db)
        user_dao.update_member(int(values[0]), username, name, email, student_id, contact)
        messagebox.showinfo("Success", "Member updated!")
        self.refresh_manage_members_tree()

    def delete_member_ctk(self, member_id):
        if messagebox.askyesno("Confirm", "Delete this member?"):
            user_dao = UserDAO(self.db)
            user_dao.delete_member(int(member_id))
            messagebox.showinfo("Success", "Member deleted!")
            self.refresh_manage_members_tree()

    def show_manage_loans(self):
        for w in self.content_area.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.content_area, text="Manage Loans", font=ctk.CTkFont(size=44, weight="bold")).pack(pady=40)

        loan_dao = LoanDAO(self.db)
        book_dao = BookDAO(self.db)
        user_dao = UserDAO(self.db)
        loans = loan_dao.get_all()
        books = {b.id: b.title for b in book_dao.get_all()}
        members = {m.member_id: m.name for m in user_dao.get_all_members()}

        style = ttk.Style()
        style.configure("Treeview", font=('Helvetica', 12), rowheight=40)
        style.configure("Treeview.Heading", font=('Helvetica', 14, 'bold'))

        self.manage_loans_tree = ttk.Treeview(self.content_area, columns=("ID", "Book Title", "Member Name", "Borrow Date", "Due Date", "Return Date", "Status"), show="headings", height=15)
        for col in self.manage_loans_tree["columns"]:
            self.manage_loans_tree.heading(col, text=col)
            self.manage_loans_tree.column(col, width=150, anchor="center")
        self.manage_loans_tree.pack(pady=20, fill="both", expand=True, padx=50)

        for loan in loans:
            self.manage_loans_tree.insert("", "end", values=(
                loan.id,
                books.get(loan.book_id, "Unknown"),
                members.get(loan.member_id, "Unknown"),
                loan.borrow_date.strftime("%Y-%m-%d"),
                loan.due_date.strftime("%Y-%m-%d"),
                loan.return_date.strftime("%Y-%m-%d") if loan.return_date else "N/A",
                loan.status
            ))

        self.manage_loans_tree.bind("<<TreeviewSelect>>", self.on_manage_loan_select)

        self.manage_loan_action_frame = ctk.CTkFrame(self.content_area)
        self.manage_loan_action_frame.pack(pady=10)

    def on_manage_loan_select(self, event):
        for w in self.manage_loan_action_frame.winfo_children():
            w.destroy()

        selected = event.widget.focus()
        if selected:
            values = event.widget.item(selected, "values")
            if values[6] in ('Active', 'Overdue'):
                return_btn = ctk.CTkButton(self.manage_loan_action_frame, text="Mark Returned", fg_color="#ef4444",
                                           command=lambda: self.return_selected_loan(values[0]))
                return_btn.pack()

    def show_manage_book_clubs(self):
        for w in self.content_area.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.content_area, text="Manage Book Clubs", font=ctk.CTkFont(size=44, weight="bold")).pack(pady=30)

        form = ctk.CTkFrame(self.content_area)
        form.pack(pady=20, fill="x", padx=100)

        labels = ["Name", "Description"]
        self.club_entries = {}
        for i, label in enumerate(labels):
            ctk.CTkLabel(form, text=label + ":", font=ctk.CTkFont(size=16)).grid(row=i, column=0, pady=10, padx=10, sticky="e")
            if label == "Description":
                self.club_entries[label] = ctk.CTkTextbox(form, width=400, height=100)
            else:
                self.club_entries[label] = ctk.CTkEntry(form, width=400, height=40)
            self.club_entries[label].grid(row=i, column=1, pady=10, padx=10)

        add_btn = ctk.CTkButton(form, text="Add Club", fg_color="#10b981", command=self.add_club_ctk)
        add_btn.grid(row=len(labels), column=0, columnspan=2, pady=20)

        style = ttk.Style()
        style.configure("Treeview", font=('Helvetica', 12), rowheight=40)
        style.configure("Treeview.Heading", font=('Helvetica', 14, 'bold'))

        self.manage_clubs_tree = ttk.Treeview(
            self.content_area,
            columns=("ID", "Name", "Description"),
            show="headings",
            height=15
        )
        for col in self.manage_clubs_tree["columns"]:
            self.manage_clubs_tree.heading(col, text=col)
            self.manage_clubs_tree.column(col, width=300, anchor="center")
        self.manage_clubs_tree.pack(pady=20, fill="both", expand=True, padx=50)

        self.manage_clubs_tree.bind("<<TreeviewSelect>>", self.on_manage_club_select)

        self.manage_club_action_frame = ctk.CTkFrame(self.content_area)
        self.manage_club_action_frame.pack(pady=10)

        self.refresh_manage_clubs_tree()

    def add_club_ctk(self):
        name = self.club_entries["Name"].get()
        desc = self.club_entries["Description"].get("1.0", "end-1c")
        if name:
            book_club_dao = BookClubDAO(self.db)
            book_club_dao.create(name, desc, self.user.id)
            messagebox.showinfo("Success", "Club added!")
            self.refresh_manage_clubs_tree()
        else:
            messagebox.showerror("Error", "Name required!")

    def refresh_manage_clubs_tree(self):
        book_club_dao = BookClubDAO(self.db)
        clubs = book_club_dao.get_all()
        for item in self.manage_clubs_tree.get_children():
            self.manage_clubs_tree.delete(item)
        for club in clubs:
            self.manage_clubs_tree.insert("", "end", values=(
                club.id,
                club.name,
                club.description
            ))

    def on_manage_club_select(self, event):
        for w in self.manage_club_action_frame.winfo_children():
            w.destroy()

        selected = event.widget.focus()
        if selected:
            values = event.widget.item(selected, "values")
            edit_btn = ctk.CTkButton(self.manage_club_action_frame, text="Edit", fg_color="#f59e0b",
                                     command=lambda: self.edit_club_ctk(values))
            edit_btn.pack(side="left", padx=5)
            delete_btn = ctk.CTkButton(self.manage_club_action_frame, text="Delete", fg_color="#ef4444",
                                       command=lambda: self.delete_club_ctk(values[0]))
            delete_btn.pack(side="left", padx=5)
            manage_btn = ctk.CTkButton(self.manage_club_action_frame, text="Manage Members", fg_color="#00d4ff",
                                       command=lambda: self.manage_club_members_ctk(values[0], values[1]))
            manage_btn.pack(side="left", padx=5)

    def edit_club_ctk(self, values):
        name = simpledialog.askstring("Edit Name", "Name:", initialvalue=values[1])
        if name is None: return
        desc = simpledialog.askstring("Edit Description", "Description:", initialvalue=values[2])
        if desc is None: return
        book_club_dao = BookClubDAO(self.db)
        book_club_dao.update(int(values[0]), name, desc)
        messagebox.showinfo("Success", "Club updated!")
        self.refresh_manage_clubs_tree()

    def delete_club_ctk(self, club_id):
        if messagebox.askyesno("Confirm", "Delete this club?"):
            book_club_dao = BookClubDAO(self.db)
            book_club_dao.delete(int(club_id))
            messagebox.showinfo("Success", "Club deleted!")
            self.refresh_manage_clubs_tree()

    def manage_club_members_ctk(self, club_id, club_name):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Manage Members for {club_name}")
        dialog.geometry("600x400")

        book_club_dao = BookClubDAO(self.db)
        user_dao = UserDAO(self.db)
        all_members = user_dao.get_all_members()
        member_dict = {m.member_id: m.name for m in all_members}
        current_members = book_club_dao.get_members(int(club_id))

        style = ttk.Style()
        style.configure("Treeview", font=('Helvetica', 12), rowheight=40)
        style.configure("Treeview.Heading", font=('Helvetica', 14, 'bold'))

        tree = ttk.Treeview(dialog, columns=("ID", "Name"), show="headings")
        tree.heading("ID", text="ID")
        tree.heading("Name", text="Name")
        tree.column("ID", width=100)
        tree.column("Name", width=400)
        tree.pack(fill="both", expand=True, pady=10, padx=10)

        self.refresh_club_members_tree(tree, int(club_id), member_dict)

        add_frame = ctk.CTkFrame(dialog)
        add_frame.pack(pady=10)

        combo_values = [m.name for m in all_members if m.member_id not in current_members]
        add_combo = ctk.CTkComboBox(add_frame, values=combo_values, width=300)
        add_combo.pack(side="left", padx=10)

        add_btn = ctk.CTkButton(add_frame, text="Add Member", fg_color="#10b981",
                                command=lambda: self.add_club_member_ctk(add_combo.get(), int(club_id), tree, add_combo, all_members, member_dict))
        add_btn.pack(side="left", padx=10)

        tree.bind("<<TreeviewSelect>>", lambda e: self.on_club_member_select(e, tree, int(club_id), add_frame, member_dict))

    def on_club_member_select(self, event, tree, club_id, add_frame, member_dict):
        remove_frame = ctk.CTkFrame(add_frame.master)  # Use the dialog as parent
        for w in add_frame.master.winfo_children():
            if isinstance(w, ctk.CTkFrame) and w != add_frame:
                w.destroy()
        remove_frame.pack(pady=10)

        selected = event.widget.focus()
        if selected:
            mid = event.widget.item(selected, "values")[0]
            remove_btn = ctk.CTkButton(remove_frame, text="Remove Selected", fg_color="#ef4444",
                                       command=lambda: self.remove_club_member_ctk(mid, club_id, tree, member_dict))
            remove_btn.pack()

    def add_club_member_ctk(self, name, club_id, tree, combo, all_members, member_dict):
        mid = next((m.member_id for m in all_members if m.name == name), None)
        if mid:
            book_club_dao = BookClubDAO(self.db)
            book_club_dao.add_member(club_id, mid)
            self.refresh_club_members_tree(tree, club_id, member_dict)
            current_members = book_club_dao.get_members(club_id)
            combo.configure(values=[m.name for m in all_members if m.member_id not in current_members])

    def remove_club_member_ctk(self, mid, club_id, tree, member_dict):
        book_club_dao = BookClubDAO(self.db)
        book_club_dao.remove_member(club_id, int(mid))
        self.refresh_club_members_tree(tree, club_id, member_dict)

    def refresh_club_members_tree(self, tree, club_id, member_dict):
        for item in tree.get_children():
            tree.delete(item)
        book_club_dao = BookClubDAO(self.db)
        current_members = book_club_dao.get_members(club_id)
        for mid in current_members:
            tree.insert("", "end", values=(mid, member_dict.get(mid, "Unknown")))

if __name__ == "__main__":
    db = Database()
    app = SmartLibraryApp(db)
    app.mainloop()



