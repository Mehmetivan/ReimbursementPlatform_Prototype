# ReimbursementPlatform_Prototype
Prototype for a subscription reimbursement web platform for students.

Description:
This prototype is a simple web platform that allows students to submit reimbursement requests for public transportation subscriptions by uploading receipts online. Administrative staff can review, approve, or reject requests. The system demonstrates a login flow with separate roles for students and staff, receipt uploads, and approval workflows, showcasing GET and POST requests and session management.

Technologies Used:

Backend: Python + Flask (handles GET/POST, session management, and request routing)
Database: SQLite (stores user accounts, receipts, and requests)
Frontend: HTML + Bootstrap (renders clean, responsive interfaces)
File Storage: Local uploads folder for receipt images
Sessions: Flask session cookies to maintain login state and roles

Key Features:

Student login and submission of reimbursement requests
Staff login for reviewing and approving/rejecting requests
Receipt image upload and storage
Session-based authentication with student and staff roles
Demonstrates GET and POST HTTP methods
