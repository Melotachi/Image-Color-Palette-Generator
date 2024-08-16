
from colorgenerator import ColorGenerator

from flask import Flask, render_template, request,redirect,url_for
from flask_sqlalchemy import SQLAlchemy

from PIL import Image

import os
import pandas as pd
import plotly.express as px
import numpy as np

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///images.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # To suppress a warning message

db = SQLAlchemy(app)

THUMBNAIL_SIZES = (434, 225) 

class ImageModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_name = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)

class ColorModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image_model.id'), nullable=False)
    color_data = db.Column(db.String(255), nullable=False)
    chart_url = db.Column(db.String(255), nullable=False)


@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        images = request.files.getlist('images[]') # Get all the images from the form

        for image in images:
            
            img = Image.open(image)
            generator = ColorGenerator(img)
            generator.generate_colors()
            img.thumbnail(THUMBNAIL_SIZES) # Resize the image to a thumbnail

            current_directory = os.getcwd()
            
            os.makedirs('static', exist_ok=True) # create static folder if it doesn't exist
            
            output_path = os.path.join(current_directory, 'static', image.filename)
            img.save(output_path) # Save the thumbnail to the static folder

            new_image = ImageModel(image_name=image.filename, image_url=image.filename) # Save the image to the database
            db.session.add(new_image)
            db.session.commit()

            df = pd.DataFrame(generator.colors[:30], columns=['count', 'color'])
            df['color'] = df['color'].apply(lambda x: f'rgb({x[0]},{x[1]},{x[2]})') # Convert the color to rgb format of plotly
            df.sort_values('count', ascending=False, inplace=True) # Sort the colors by count in descending order

            fig = px.bar(df, x=df.index, y='count', color='color', color_discrete_sequence=df['color'].unique(),
                         labels={'index': 'Colors', 'count': 'Count'},
                         title='Color Distribution')
            
            fig.update_xaxes(
                tickvals=np.arange(0, len(df), 1),
                title_text='Colors'
            )
            
            fig.update_layout(
                title={
                    'text': 'Color Distribution',
                    'x': 0.5,
                    'xanchor': 'center'
                }
            )

            chart_name = f'color_distribution_{new_image.id}.png'
            chart_path = os.path.join('static', chart_name)
            fig.write_image(chart_path) # Save the chart to the static folder

            new_color = ColorModel(image_id=new_image.id, color_data=str(generator.colors[:30]), chart_url=chart_name) # Save the color data to the database
            db.session.add(new_color)
            db.session.commit()
            
        return redirect(url_for('main')) # By doing so, when we refresh the page, the form will be empty

    images_data = ImageModel.query.all() # Get all the images from the database
    colors_data = ColorModel.query.all() # Get all the color data from the database
    
    everything = list(zip(images_data, colors_data)) # Combine the images and color data

    return render_template('index.html', everything=everything)

@app.route('/delete',methods=['POST']) 
def delete(): # This function is used to delete an image and its color data
    
    image_name = request.form['image_name']
    chart_url = request.form['chart_url']
    
    image = ImageModel.query.filter_by(image_name=image_name).first()
    color = ColorModel.query.filter_by(chart_url=chart_url).first()

    if image:
        db.session.delete(image)
        db.session.commit()

    if color:
        db.session.delete(color)
        db.session.commit()

    return redirect(url_for('main'))


if __name__ == '__main__':
        
    if os.path.exists('static'): # Delete all the files in the static folder at the start of the application (optional)
        for file in os.listdir('static'):
            os.remove(os.path.join('static', file))
    
    with app.app_context():
        db.drop_all() # Drop all the tables at the start of the application (optional)
        db.create_all()
        
    app.run(debug=True)
