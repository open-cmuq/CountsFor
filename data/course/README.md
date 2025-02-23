### Prereqs Table

The **Prereqs** table stores prerequisite courses for each course and supports both simple and complex logic by using a group identifier.

- **course_code**: The course that has prerequisites.
- **prerequisite**: A course that is required.
- **logic_type**:  
  - `ANY`: Only one course in the group is needed.
  - `ALL`: Every course in the group is required.
- **group_id**: Groups related prerequisites. Multiple groups for a course imply an OR relationship.

**Examples:**

- **Simple OR**:  
  *Group 1 (logic_type = ANY)* with courses A, B, C means completing any one of A, B, or C is sufficient.

- **Complex (AND within OR)**:  
  *Group 1 (logic_type = ALL)* with courses A and B means both A and B are required.  
  *Group 2 (logic_type = ALL)* with courses C and D means both C and D are required.  
  The overall prerequisite is satisfied if either Group 1 or Group 2 is completed.
