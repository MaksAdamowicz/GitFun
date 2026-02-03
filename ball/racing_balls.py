import turtle
import random

# --- 1. Screen Setup ---
screen = turtle.Screen()
screen.setup(width=800, height=600)
screen.bgcolor("forestgreen")  # Makes it look like a turf field
screen.title("The Great Ball Race")

# --- 2. Draw the Track ---
# We use a 'pen' turtle just to draw lines, then hide it
pen = turtle.Turtle()
pen.speed(0) # Fastest drawing speed
pen.color("white")
pen.hideturtle()

def draw_finish_line():
    pen.penup()
    pen.goto(350, 250)
    pen.pendown()
    pen.width(5)
    pen.right(90)
    pen.forward(500)
    pen.penup()
    
    # Label the finish line
    pen.goto(360, 0)
    pen.write("FINISH", align="left", font=("Arial", 14, "bold"))

def draw_lanes(y_positions):
    pen.width(2)
    for y in y_positions:
        # Draw a subtle lane line under the ball path
        pen.penup()
        pen.goto(-360, y - 20)
        pen.pendown()
        pen.goto(350, y - 20)
        pen.penup()

# Define positions and colors
colors = ["red", "orange", "yellow", "cyan", "blue", "purple"]
y_positions = [150, 100, 50, 0, -50, -100]

draw_finish_line()
draw_lanes(y_positions)

# --- 3. Create the Balls ---
all_balls = []

for index in range(0, 6):
    new_ball = turtle.Turtle(shape="circle")
    new_ball.color(colors[index])
    new_ball.shapesize(stretch_wid=1.5, stretch_len=1.5) # Make balls slightly bigger
    new_ball.penup()
    new_ball.goto(x=-380, y=y_positions[index])
    all_balls.append(new_ball)

# --- 4. The Betting System ---
# Popup to ask user for input
user_bet = screen.textinput(title="Place your bet", prompt="Which color will win? (red, orange, yellow, cyan, blue, purple):")

# --- 5. The Race Loop ---
if user_bet:
    is_race_on = True
else:
    is_race_on = False

winner = None

while is_race_on:
    for ball in all_balls:
        # Check if a ball has crossed the finish line (x = 350)
        if ball.xcor() > 330: # 330 accounts for the size of the ball hitting the line
            is_race_on = False
            winner = ball.pencolor()
            
            # Celebrate the winner
            ball.shapesize(stretch_wid=2.5, stretch_len=2.5) # Winner gets huge
        
        # Move the ball a random amount
        rand_distance = random.randint(0, 15) # Random speed creates the "race" effect
        ball.forward(rand_distance)

# --- 6. Display Results ---
pen.penup()
pen.goto(0, 200)
pen.color("white")

if winner:
    if winner == user_bet:
        result_text = f"YOU WIN! The {winner} ball won the race!"
    else:
        result_text = f"YOU LOSE! The {winner} ball won, not {user_bet}."
        
    pen.write(result_text, align="center", font=("Arial", 24, "bold"))
    print(result_text)

screen.exitonclick()