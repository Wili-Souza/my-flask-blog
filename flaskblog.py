from app import app # importing the app to execute it

# this condition will be true when running directly, not when imported
if __name__ == "__main__": 
    app.run(debug=True)

