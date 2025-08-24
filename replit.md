# Overview

Escola Sol Maior is a comprehensive music school management system built with Flask. The application manages students, teachers, courses, rooms, payments, and materials for a music education institution. It provides role-based dashboards for administrators, teachers, and students, with features for enrollment management, scheduling, financial tracking, and material distribution.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM for database operations
- **Database**: PostgreSQL as the primary data store with connection pooling and health checks
- **Authentication**: Flask-Login for session management with role-based access control (admin, secretary, teacher, student)
- **Form Handling**: WTForms with CSRF protection for secure form processing
- **Email System**: Flask-Mail integrated with SMTP for notifications and communications

## Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 for responsive UI
- **Styling**: Custom CSS with CSS variables for theming, Font Awesome icons
- **JavaScript**: Vanilla JavaScript with Bootstrap components for interactivity
- **File Handling**: Secure file upload system with type validation and size limits (16MB max)

## Data Model Design
- **User Management**: Hierarchical user system with profiles for students and teachers
- **Academic Management**: Course, enrollment, and scheduling entities with many-to-many relationships
- **Financial System**: Payment tracking with discount support and status management
- **Resource Management**: Material upload and distribution system organized by courses
- **Infrastructure**: Room and equipment management with capacity tracking

## Security Features
- **CSRF Protection**: Cross-site request forgery prevention on all forms
- **Password Security**: Werkzeug password hashing for user credentials
- **File Security**: Whitelist-based file type validation and secure filename handling
- **Proxy Support**: ProxyFix middleware for deployment behind reverse proxies
- **Session Management**: Secure session handling with configurable secret keys

## Application Structure
- **Blueprint Organization**: Modular route organization (main, auth, admin, student, teacher, public)
- **Form Architecture**: Dedicated form classes for each entity with validation
- **Utility Functions**: Centralized helpers for email, file handling, and formatting
- **Template Inheritance**: Base template system with role-specific layouts

# External Dependencies

## Core Framework Dependencies
- **Flask**: Web application framework with SQLAlchemy integration
- **Flask-Login**: User session management and authentication
- **Flask-Mail**: Email sending capabilities for notifications
- **Flask-WTF**: Form handling with CSRF protection
- **WTForms**: Form validation and rendering
- **Werkzeug**: WSGI utilities and security helpers

## Database and Data Processing
- **SQLAlchemy**: ORM with PostgreSQL adapter
- **PostgreSQL**: Primary database with connection pooling configuration

## Frontend Libraries
- **Bootstrap 5**: CSS framework delivered via CDN
- **Font Awesome 6**: Icon library for UI elements
- **Vanilla JavaScript**: No heavy frontend frameworks, using native browser APIs

## Infrastructure Services
- **SMTP Email Service**: Configurable email provider (default: Gmail SMTP)
- **File Storage**: Local filesystem storage with upload directory management
- **Environment Configuration**: Environment-based configuration for deployment flexibility

## Development and Production Tools
- **ProxyFix**: Werkzeug middleware for reverse proxy deployment
- **Logging**: Python's built-in logging system for debugging and monitoring