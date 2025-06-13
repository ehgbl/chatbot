from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import json
import os

app = Flask(__name__)
CORS(app)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Product data
DRESS_DATA = {
    "styles": {
        "classic": {"base_price": 120, "description": "Timeless A-line dress with elegant silhouette"},
        "bohemian": {"base_price": 135, "description": "Flowing maxi dress with artistic flair"},
        "cocktail": {"base_price": 145, "description": "Sophisticated knee-length dress for special occasions"},
        "casual": {"base_price": 95, "description": "Comfortable everyday dress with relaxed fit"}
    },
    "colors": ["blue", "brown", "green", "yellow"],
    "sizes": {
        "XS": {"bust": 32, "waist": 24, "hips": 34},
        "S": {"bust": 34, "waist": 26, "hips": 36},
        "M": {"bust": 36, "waist": 28, "hips": 38},
        "L": {"bust": 38, "waist": 30, "hips": 40},
        "XL": {"bust": 40, "waist": 32, "hips": 42}
    },
    "customizations": {
        "embroidery": {"floral": 25, "geometric": 20, "custom": 35},
        "buttons": {"pearl": 15, "wooden": 10, "metal": 12},
        "tailoring": {"custom_fit": 30, "length_adjustment": 15}
    },
    "delivery": {
        "standard": "2-3 weeks",
        "rush": "1 week (+$40)"
    }
}

SYSTEM_PROMPT = f"""
You are a helpful assistant for a handmade dress company. Use this information:

PRODUCTS: {json.dumps(DRESS_DATA, indent=2)}

GUIDELINES:
- Help customers choose sizes, styles, colors, and customizations
- Calculate total prices including customizations
- Explain delivery times and rush options
- Provide care instructions for handmade dresses
- Be friendly and knowledgeable about fashion

CARE INSTRUCTIONS:
- Hand wash or delicate cycle
- Air dry only
- Iron on low heat
- Store hanging to prevent wrinkles

Always be helpful and specific with recommendations.
"""

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message', '')
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        bot_response = response.choices[0].message.content.strip()
        
        return jsonify({
            "response": bot_response,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({
            "response": "I'm having trouble right now. Please try again later.",
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/products', methods=['GET'])
def get_products():
    """Return product catalog for reference"""
    return jsonify(DRESS_DATA)

@app.route('/calculate-price', methods=['POST'])
def calculate_price():
    """Calculate total price with customizations"""
    try:
        data = request.json
        style = data.get('style', '').lower()
        customizations = data.get('customizations', {})
        
        if style not in DRESS_DATA['styles']:
            return jsonify({"error": "Invalid style"}), 400
            
        base_price = DRESS_DATA['styles'][style]['base_price']
        total_price = base_price
        
        # Add customization costs
        if 'embroidery' in customizations:
            embroidery_type = customizations['embroidery']
            if embroidery_type in DRESS_DATA['customizations']['embroidery']:
                total_price += DRESS_DATA['customizations']['embroidery'][embroidery_type]
        
        if 'buttons' in customizations:
            button_type = customizations['buttons']
            if button_type in DRESS_DATA['customizations']['buttons']:
                total_price += DRESS_DATA['customizations']['buttons'][button_type]
        
        if 'tailoring' in customizations:
            tailoring_type = customizations['tailoring']
            if tailoring_type in DRESS_DATA['customizations']['tailoring']:
                total_price += DRESS_DATA['customizations']['tailoring'][tailoring_type]
        
        if data.get('rush_order'):
            total_price += 40
            
        return jsonify({
            "base_price": base_price,
            "total_price": total_price,
            "breakdown": customizations
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/size-recommendation', methods=['POST'])
def size_recommendation():
    """Recommend size based on measurements"""
    try:
        measurements = request.json
        user_bust = measurements.get('bust', 0)
        user_waist = measurements.get('waist', 0)
        user_hips = measurements.get('hips', 0)
        
        best_size = None
        min_difference = float('inf')
        
        for size, size_measurements in DRESS_DATA['sizes'].items():
            # Calculate total difference from ideal measurements
            diff = (abs(size_measurements['bust'] - user_bust) + 
                   abs(size_measurements['waist'] - user_waist) + 
                   abs(size_measurements['hips'] - user_hips))
            
            if diff < min_difference:
                min_difference = diff
                best_size = size
        
        return jsonify({
            "recommended_size": best_size,
            "size_measurements": DRESS_DATA['sizes'][best_size],
            "note": "Consider custom tailoring for perfect fit"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)