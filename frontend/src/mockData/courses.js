const mockCourses = [
    {
      course_code: "76-239",
      course_name: "Introduction to Film Studies",
      requirements: {
        CS: ["Cultural Analysis"],
        IS: ["The Arts"],
        BA: ["Global, Cultural, Diverse Perspectives"],
        BS: ["Cultural/Global Understanding"],
      },
      offered: ["Spring 25", "Fall 24"],
      prerequisites: "None",
    },
    {
      course_code: "76-270",
      course_name: "Writing for Professions",
      requirements: {
        CS: ["Technical Communication"],
        IS: ["Additional Disciplines"],
        BA: ["Global, Cultural, Diverse Perspectives"],
        BS: [],
      },
      offered: ["Spring 25", "Spring 24"],
      prerequisites: "None",
    },
    {
        course_code: "15-150",
        course_name: "Foundations of Functional Programming",
        requirements: {
          CS: ["CORE"],
          IS: [],
          BA: [],
          BS: ["Mathematics, Statistics, and Computer Science", "STEM Course"],
        },
        offered: ["Spring 25", "Spring 24"],
        prerequisites: "None",
      },
      {
        course_code: "79-104",
        course_name: "Global Histories",
        requirements: {
          CS: ["Cultural Analysis"],
          IS: ["Humanities"],
          BA: ["Global, Cultural, Diverse Perspectives"],
          BS: ["Cultural/Global Understanding"],
        },
        offered: ["Spring 25", "Spring 24"],
        prerequisites: "None",
      },
  ];
  
  export default mockCourses;
  