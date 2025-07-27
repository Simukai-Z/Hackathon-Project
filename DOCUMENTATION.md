# StudyCoach Platform Documentation

## New Features (July 2025)

### Multi-Teacher Classrooms
- Teachers can now create new classes and invite or join as co-teachers.
- Each classroom supports multiple teachers via the `teacher_emails` field.
- Teachers can manage assignments, students, and rubrics collaboratively.

### Modern Join Classroom Experience
- The join classroom page (`/classroom/join/<code>`) is now fully modernized with a responsive, theme-aware design.
- Light and dark mode are supported everywhere, including join and confirmation pages.
- The join confirmation page is also modernized and theme-aware.

### Copy Class Join Link for Teachers
- Teachers can copy the class join link from their dashboard with a single click.
- The link is copied to the clipboard and a toast notification confirms success.

### UI/UX Improvements
- All modals and forms use a modern, consistent design system.
- Theme toggling is available on all major pages.
- Accessibility and mobile responsiveness improved for all join and class management flows.

## API Endpoints
- `POST /api/create_class`: Create a new class (teacher only)
- `POST /api/join_class_as_teacher`: Join an existing class as a teacher
- `GET /api/my_classes`: List classes managed or joined by the current teacher

## How to Use
- Teachers: Create or join classes from the dashboard sidebar. Use the "Copy Link" button to share the join link with students.
- Students: Use the join link or code to join a class. The join and confirmation pages are now modern and theme-aware.

## Upgrading
- Existing classrooms will be automatically upgraded to support multiple teachers.
- No manual migration required for users or assignments.

## See Also
- [README.md](../README.md) for setup and installation instructions.
- [docs/](./docs/) for additional technical and feature documentation.

---

_Last updated: July 27, 2025_
