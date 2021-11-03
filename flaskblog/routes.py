import os
import secrets
from PIL import Image, ImageTk
from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app, db, bcrypt
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm
from flaskblog.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask import Flask, render_template, request, Response, url_for
import numpy as np
import math
import cv2
from easygui import *

import speech_recognition as sr
import matplotlib.pyplot as plt
import string
import tkinter as tk
from itertools import count


@app.route("/")
@app.route("/home")
def home():
    posts = Post.query.all()
    return render_template('home.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title='About')
    


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))

@app.route("/translator", methods=['GET', 'POST'])
def translator():
    if request.method == 'POST':
        if request.form.get('action1') == 'Sign to Text':
            cap = cv2.VideoCapture(0)

            while (1):

                try:  # an error comes if it does not find anything in window as it cannot find contour of max area
                    # therefore this try error statement

                    ret, frame = cap.read()
                    frame = cv2.flip(frame, 1)
                    kernel = np.ones((3, 3), np.uint8)

                    # define region of interest
                    roi = frame[100:300, 100:300]

                    cv2.rectangle(frame, (100, 100), (300, 300), (0, 255, 0), 0)
                    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

                    # define range of skin color in HSV
                    lower_skin = np.array([0, 20, 70], dtype=np.uint8)
                    upper_skin = np.array([20, 255, 255], dtype=np.uint8)

                    # extract skin colur imagw
                    mask = cv2.inRange(hsv, lower_skin, upper_skin)

                    # extrapolate the hand to fill dark spots within
                    mask = cv2.dilate(mask, kernel, iterations=4)

                    # blur the image
                    mask = cv2.GaussianBlur(mask, (5, 5), 100)

                    # find contours
                    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                    # find contour of max area(hand)
                    # screen has no readable parts
                    if contours == [] and hierarchy == None:
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        cv2.putText(frame, 'Nothig is visible', (0, 50), font, 2, (0, 0, 255), 3, cv2.LINE_AA)
                        cv2.imshow('frame', frame)
                        cv2.waitKey(1)
                        continue

                    cnt = max(contours, key=lambda x: cv2.contourArea(x))

                    # approx the contour a little
                    epsilon = 0.0005 * cv2.arcLength(cnt, True)
                    approx = cv2.approxPolyDP(cnt, epsilon, True)

                    # make convex hull around hand
                    hull = cv2.convexHull(cnt)

                    # define area of hull and area of hand
                    areahull = cv2.contourArea(hull)
                    areacnt = cv2.contourArea(cnt)

                    # find the percentage of area not covered by hand in convex hull
                    arearatio = ((areahull - areacnt) / areacnt) * 100

                    # find the defects in convex hull with respect to hand
                    hull = cv2.convexHull(approx, returnPoints=False)
                    defects = cv2.convexityDefects(approx, hull)

                    # l = no. of defects
                    l = 0

                    # code for finding no. of defects due to fingers
                    for i in range(defects.shape[0]):
                        s, e, f, d = defects[i, 0]
                        start = tuple(approx[s][0])
                        end = tuple(approx[e][0])
                        far = tuple(approx[f][0])
                        pt = (100, 180)

                        # find length of all sides of triangle
                        a = math.sqrt((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2)
                        b = math.sqrt((far[0] - start[0]) ** 2 + (far[1] - start[1]) ** 2)
                        c = math.sqrt((end[0] - far[0]) ** 2 + (end[1] - far[1]) ** 2)
                        s = (a + b + c) / 2
                        ar = math.sqrt(s * (s - a) * (s - b) * (s - c))

                        # distance between point and convex hull
                        d = (2 * ar) / a

                        # apply cosine rule here
                        angle = math.acos((b ** 2 + c ** 2 - a ** 2) / (2 * b * c)) * 57

                        # ignore angles > 90 and ignore points very close to convex hull(they generally come due to noise)
                        if angle <= 90 and d > 30:
                            l += 1
                            cv2.circle(roi, far, 3, [255, 0, 0], -1)

                        # draw lines around hand
                        cv2.line(roi, start, end, [0, 255, 0], 2)

                    l += 1

                    # print corresponding gestures which are in their ranges
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    if l == 1:
                        if areacnt < 2000:
                            cv2.putText(frame, 'Put hand in the box', (0, 50), font, 2, (0, 0, 255), 3, cv2.LINE_AA)
                        else:
                            if arearatio < 12:
                                cv2.putText(frame, '0', (0, 50), font, 2, (0, 0, 255), 3, cv2.LINE_AA)
                            elif arearatio < 17.5:
                                cv2.putText(frame, 'Best of luck', (0, 50), font, 2, (0, 0, 255), 3, cv2.LINE_AA)

                            else:
                                cv2.putText(frame, '1', (0, 50), font, 2, (0, 0, 255), 3, cv2.LINE_AA)

                    elif l == 2:
                        cv2.putText(frame, '2', (0, 50), font, 2, (0, 0, 255), 3, cv2.LINE_AA)

                    elif l == 3:

                        if arearatio < 27:
                            cv2.putText(frame, '3', (0, 50), font, 2, (0, 0, 255), 3, cv2.LINE_AA)
                        else:
                            cv2.putText(frame, 'ok', (0, 50), font, 2, (0, 0, 255), 3, cv2.LINE_AA)

                    elif l == 4:
                        cv2.putText(frame, '4', (0, 50), font, 2, (0, 0, 255), 3, cv2.LINE_AA)

                    elif l == 5:
                        cv2.putText(frame, '5', (0, 50), font, 2, (0, 0, 255), 3, cv2.LINE_AA)

                    elif l == 6:
                        cv2.putText(frame, 'reposition', (0, 50), font, 2, (0, 0, 255), 3, cv2.LINE_AA)

                    else:
                        cv2.putText(frame, 'reposition', (10, 50), font, 2, (0, 0, 255), 3, cv2.LINE_AA)

                    # show the windows
                    cv2.imshow('mask', mask)
                    cv2.imshow('frame', frame)
                except Exception as e:
                    pass
                    # print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), e)

                k = cv2.waitKey(5) & 0xFF
                if k == 27:
                    break

            cv2.destroyAllWindows()
            cap.release()

        elif request.form.get('action2') == 'Text to Sign':
            def func():
                r = sr.Recognizer()
                isl_gif = ['all the best', 'any questions', 'are you angry', 'are you busy', 'are you hungry',
                           'are you sick',
                           'be careful',
                           'can we meet tomorrow', 'did you book tickets', 'did you finish homework',
                           'do you go to office',
                           'do you have money',
                           'do you want something to drink', 'do you want tea or coffee', 'do you watch TV',
                           'dont worry',
                           'flower is beautiful',
                           'good afternoon', 'good evening', 'good morning', 'good night', 'good question',
                           'had your lunch',
                           'happy journey',
                           'hello what is your name', 'how many people are there in your family', 'i am a clerk',
                           'i am bore doing nothing',
                           'i am fine', 'i am sorry', 'i am thinking', 'i am tired', 'i dont understand anything',
                           'i go to a theatre', 'i love to shop',
                           'i had to say something but i forgot', 'i have headache', 'i like pink colour',
                           'i live in nagpur',
                           'lets go for lunch', 'my mother is a homemaker',
                           'my name is john', 'nice to meet you', 'no smoking please', 'open the door',
                           'please call an ambulance',
                           'please call me later',
                           'please clean the room', 'please give me your pen', 'please use dustbin dont throw garbage',
                           'please wait for sometime', 'shall I help you',
                           'shall we go together tomorrow', 'sign language interpreter', 'sit down', 'stand up',
                           'take care',
                           'there was traffic jam', 'wait I am thinking',
                           'what are you doing', 'what is the problem', 'what is todays date', 'what is your age',
                           'what is your father do', 'what is your job',
                           'what is your mobile number', 'what is your name', 'whats up', 'when is your interview',
                           'when we will go', 'where do you stay',
                           'where is the bathroom', 'where is the police station', 'you are wrong', 'address', 'agra',
                           'ahemdabad',
                           'all', 'april', 'assam', 'august', 'australia', 'badoda', 'banana', 'banaras', 'banglore',
                           'bihar', 'bihar', 'bridge', 'cat', 'chandigarh', 'chennai', 'christmas', 'church', 'clinic',
                           'coconut',
                           'crocodile', 'dasara',
                           'deaf', 'december', 'deer', 'delhi', 'dollar', 'duck', 'febuary', 'friday', 'fruits',
                           'glass', 'grapes',
                           'gujrat', 'hello',
                           'hindu', 'hyderabad', 'india', 'january', 'jesus', 'job', 'july', 'july', 'karnataka',
                           'kerala',
                           'krishna', 'litre', 'mango',
                           'may', 'mile', 'monday', 'mumbai', 'museum', 'muslim', 'nagpur', 'october', 'orange',
                           'pakistan', 'pass',
                           'police station',
                           'post office', 'pune', 'punjab', 'rajasthan', 'ram', 'restaurant', 'saturday', 'september',
                           'shop',
                           'sleep', 'southafrica',
                           'story', 'sunday', 'tamil nadu', 'temperature', 'temple', 'thursday', 'toilet', 'tomato',
                           'town',
                           'tuesday', 'usa', 'village',
                           'voice', 'wednesday', 'weight']

                arr = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r',
                       's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
                with sr.Microphone() as source:

                    r.adjust_for_ambient_noise(source)
                    i = 0
                    while True:
                        print('Say something')
                        audio = r.listen(source)

                        # recognize speech using Sphinx
                        try:
                            a = r.recognize_google(audio)
                            print("you said " + a.lower())

                            for c in string.punctuation:
                                a = a.replace(c, "")

                            if (a.lower() == 'goodbye'):
                                print("oops!Time To say good bye")
                                break

                            elif (a.lower() in isl_gif):

                                class ImageLabel(tk.Label):
                                    """a label that displays images, and plays them if they are gifs"""

                                    def load(self, im):
                                        if isinstance(im, str):
                                            im = Image.open(im)
                                        self.loc = 0
                                        self.frames = []

                                        try:
                                            for i in count(1):
                                                self.frames.append(ImageTk.PhotoImage(im.copy()))
                                                im.seek(i)
                                        except EOFError:
                                            pass

                                        try:
                                            self.delay = im.info['duration']
                                        except:
                                            self.delay = 100

                                        if len(self.frames) == 1:
                                            self.config(image=self.frames[0])
                                        else:
                                            self.next_frame()

                                    def unload(self):
                                        self.config(image=None)
                                        self.frames = None

                                    def next_frame(self):
                                        if self.frames:
                                            self.loc += 1
                                            self.loc %= len(self.frames)
                                            self.config(image=self.frames[self.loc])
                                            self.after(self.delay, self.next_frame)

                                root = tk.Tk()
                                lbl = ImageLabel(root)
                                lbl.pack()
                                lbl.load(r'C:\Users\Poonam\Desktop\MegaProject'.format(a.lower()))
                                root.mainloop()
                            else:

                                for i in range(len(a)):
                                    if (a[i] in arr):

                                        ImageAddress = 'letters/' + a[i] + '.jpg'
                                        ImageItself = Image.open(ImageAddress)
                                        ImageNumpyFormat = np.asarray(ImageItself)
                                        plt.imshow(ImageNumpyFormat)
                                        plt.draw()
                                        plt.pause(0.8) 
                                    else:
                                        continue

                        except:
                            print("Could not listen")
                        plt.close()

            while 1:
                image = "ISL.png"
                msg = "HEARING IMPAIRMENT ASSISTANT"
                choices = ["Live Voice", "All Done!"]
                reply = buttonbox(msg, image=image, choices=choices)
                if reply == choices[0]:
                    func()
                if reply == choices[1]:
                    exit()

        else:
            pass
    elif request.method == 'GET':
        return render_template('translator.html', title='Translator')

    return render_template("translator.html", title='Translator')


if __name__ == "__main__":
    app.run(debug=True)