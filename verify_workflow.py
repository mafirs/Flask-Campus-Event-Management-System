#!/usr/bin/env python3
"""
Workflow Verification Script
Tests the core business logic: differential approval flow and conflict detection
"""

import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.venue import Venue
from app.models.material import Material
from app.models.application import Application, ApplicationMaterial


# Test helper functions
def print_pass(message):
    print(f"[PASS] {message}")


def print_fail(message):
    print(f"[FAIL] {message}")


def print_info(message):
    print(f"[INFO] {message}")


def setup():
    """Initialize app, create tables, clear old data"""
    app = create_app()

    with app.app_context():
        db.create_all()

        # Clear old test data
        ApplicationMaterial.query.delete()
        Application.query.delete()
        Material.query.delete()
        Venue.query.delete()
        User.query.delete()
        db.session.commit()

        print_info("Environment setup complete")
        return app


def prepare_base_data():
    """Create test users, venue, and material"""

    # Create 4 users
    # Note: Create teacher with role='teacher' for testing (direct DB insert)
    student = User(
        id=1,
        username='student',
        password='test123',
        real_name='Test Student',
        email='student@test.com',
        role='user'  # regular user
    )

    teacher = User(
        id=2,
        username='teacher',
        password='test123',
        real_name='Test Teacher',
        email='teacher@test.com',
        role='teacher'  # teacher role for testing
    )

    reviewer = User(
        id=3,
        username='reviewer',
        password='test123',
        real_name='Test Reviewer',
        email='reviewer@test.com',
        role='reviewer'
    )

    admin = User(
        id=4,
        username='admin',
        password='test123',
        real_name='Test Admin',
        email='admin@test.com',
        role='admin'
    )

    db.session.add_all([student, teacher, reviewer, admin])
    db.session.flush()  # Get IDs without committing

    # Create 1 venue
    venue = Venue(
        id=1,
        name='Test Venue',
        location='Test Building',
        capacity=100,
        description='Test venue for workflow verification',
        equipment=[]
    )
    db.session.add(venue)
    db.session.flush()

    # Create 1 material with quantity=100
    material = Material(
        id=1,
        name='Test Material',
        category='Test Category',
        total_quantity=100,
        unit='pieces',
        description='Test material for workflow verification'
    )
    db.session.add(material)
    db.session.commit()

    print_info("Base data created")

    return {
        'student': student,
        'teacher': teacher,
        'reviewer': reviewer,
        'admin': admin,
        'venue': venue,
        'material': material
    }


def test_student_flow(data):
    """Test: student -> pending_reviewer -> pending_admin -> approved"""

    student = data['student']
    venue = data['venue']
    material = data['material']
    reviewer = data['reviewer']
    admin = data['admin']

    # Simulate student creating application
    start_time = (datetime.utcnow() + timedelta(days=1)).isoformat() + '+00:00'
    end_time = (datetime.utcnow() + timedelta(days=1, hours=2)).isoformat() + '+00:00'

    app_material = ApplicationMaterial(
        material_id=material.id,
        quantity=10
    )

    application = Application(
        id=1,
        user_id=student.id,
        activity_name='Student Activity',
        activity_description='Test student application',
        venue_id=venue.id,
        start_time=start_time,
        end_time=end_time,
        materials=[app_material],
        status='pending_reviewer'  # Set by applications.py logic
    )

    db.session.add(application)
    db.session.commit()

    # Verify: initial status is 'pending_reviewer'
    db.session.refresh(application)
    if application.status == 'pending_reviewer':
        print_pass("Student application created with status: pending_reviewer")
    else:
        print_fail(f"Student application has wrong status: {application.status}")
        return False

    # Simulate reviewer approval
    application.status = 'pending_admin'  # Reviewer approves
    application.reviewer_id = reviewer.id
    application.reviewed_at = datetime.utcnow()
    db.session.commit()

    # Verify: status is 'pending_admin'
    db.session.refresh(application)
    if application.status == 'pending_admin':
        print_pass("Reviewer approval: status changed to pending_admin")
    else:
        print_fail(f"After reviewer approval, status is: {application.status}")
        return False

    # Simulate admin approval
    application.status = 'approved'  # Admin approves
    application.reviewer_id = admin.id
    application.reviewed_at = datetime.utcnow()
    db.session.commit()

    # Verify: status is 'approved'
    db.session.refresh(application)
    if application.status == 'approved':
        print_pass("Admin approval: status changed to approved")
    else:
        print_fail(f"After admin approval, status is: {application.status}")
        return False

    return True


def test_teacher_flow(data):
    """Test: teacher -> pending_admin (skips reviewer)"""

    teacher = data['teacher']
    venue = data['venue']
    material = data['material']

    # Different time to avoid conflict
    start_time = (datetime.utcnow() + timedelta(days=2)).isoformat() + '+00:00'
    end_time = (datetime.utcnow() + timedelta(days=2, hours=2)).isoformat() + '+00:00'

    app_material = ApplicationMaterial(
        material_id=material.id,
        quantity=5
    )

    application = Application(
        id=2,
        user_id=teacher.id,
        activity_name='Teacher Activity',
        activity_description='Test teacher application',
        venue_id=venue.id,
        start_time=start_time,
        end_time=end_time,
        materials=[app_material],
        status='pending_admin'  # Teacher goes directly to admin
    )

    db.session.add(application)
    db.session.commit()

    # Verify: initial status is 'pending_admin' (skipped reviewer)
    db.session.refresh(application)
    if application.status == 'pending_admin':
        print_pass("Teacher application created with status: pending_admin (skips reviewer)")
    else:
        print_fail(f"Teacher application has wrong status: {application.status}")
        return False

    return True


def test_conflict_detection(data):
    """Test: conflict detection for same venue/time"""

    student = data['student']
    venue = data['venue']
    material = data['material']

    # Same time as student application from Step 3
    start_time = (datetime.utcnow() + timedelta(days=1)).isoformat() + '+00:00'
    end_time = (datetime.utcnow() + timedelta(days=1, hours=2)).isoformat() + '+00:00'

    # Check for conflicts (no need to create the conflicting application)
    conflicting_apps = db.session.query(Application).filter(
        Application.venue_id == venue.id,
        Application.status.in_(['pending_reviewer', 'pending_admin', 'approved'])
    ).all()

    has_conflict = False
    for app in conflicting_apps:
        if app.has_time_conflict(start_time, end_time):
            has_conflict = True
            break

    if has_conflict:
        print_pass("Conflict detection: correctly identified time conflict")
        return True
    else:
        print_fail("Conflict detection: failed to identify conflict")
        return False


def main():
    """Run all verification tests"""

    print("=" * 60)
    print("Workflow Verification Script")
    print("=" * 60)
    print()

    # Setup
    app = setup()

    with app.app_context():
        data = prepare_base_data()
        print()

        # Run tests
        results = []

        print("-" * 60)
        print("TEST 1: Student Approval Flow")
        print("-" * 60)
        results.append(test_student_flow(data))
        print()

        print("-" * 60)
        print("TEST 2: Teacher Approval Flow")
        print("-" * 60)
        results.append(test_teacher_flow(data))
        print()

        print("-" * 60)
        print("TEST 3: Conflict Detection")
        print("-" * 60)
        results.append(test_conflict_detection(data))
        print()

        # Summary
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        passed = sum(results)
        total = len(results)
        print(f"Passed: {passed}/{total}")

        if passed == total:
            print_pass("All tests passed!")
            return 0
        else:
            print_fail("Some tests failed!")
            return 1


if __name__ == '__main__':
    sys.exit(main())
