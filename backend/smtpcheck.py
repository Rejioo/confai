import smtplib

server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login("rajitkumaran27@gmail.com", "Xoagera@001")
print("LOGIN OK")
server.quit()
