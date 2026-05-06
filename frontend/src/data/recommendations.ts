import type { CareerRecommendation } from "../types";

export const MOCK_RECOMMENDATIONS: CareerRecommendation[] = [
  {
    id: "fullstack",
    rank: 1,
    title: "Full Stack Developer",
    description: "Build complete web applications from front-end to back-end",
    avgSalary: "6,250K EGP",
    growth: "+18%",
    matchScore: 0,
    skillGaps: [
      {
        name: "JavaScript",
        current: "Beginner",
        target: "Advanced",
        progress: 15,
        courses: [
          {
            title: "JavaScript: The Complete Guide",
            platform: "Udemy",
            duration: "52 hours",
            url: "https://www.udemy.com/course/javascript-the-complete-guide/",
          },
          {
            title: "Modern JavaScript From The Beginning",
            platform: "Coursera",
            duration: "40 hours",
            url: "https://www.coursera.org/learn/modern-javascript",
          },
        ],
      },
      {
        name: "React",
        current: "Beginner",
        target: "Advanced",
        progress: 10,
        courses: [
          {
            title: "React - The Complete Guide",
            platform: "Udemy",
            duration: "48 hours",
            url: "https://www.udemy.com/course/react-the-complete-guide/",
          },
          {
            title: "Advanced React Patterns",
            platform: "Frontend Masters",
            duration: "6 hours",
            url: "https://frontendmasters.com/courses/advanced-react-patterns/",
          },
        ],
      },
      {
        name: "Node.js",
        current: "Beginner",
        target: "Advanced",
        progress: 10,
        courses: [
          {
            title: "The Complete Node.js Developer Course",
            platform: "Udemy",
            duration: "35 hours",
            url: "https://www.udemy.com/course/the-complete-nodejs-developer-course/",
          },
          {
            title: "Node.js, Express & MongoDB Bootcamp",
            platform: "Udemy",
            duration: "42 hours",
            url: "https://www.udemy.com/course/nodejs-express-mongodb-bootcamp/",
          },
        ],
      },
    ],
  },
  {
    id: "aiml",
    rank: 2,
    title: "AI/ML Engineer",
    description: "Design and deploy machine learning models and AI systems",
    avgSalary: "7,250K EGP",
    growth: "+35%",
    matchScore: 0,
    skillGaps: [
      {
        name: "Python",
        current: "Beginner",
        target: "Advanced",
        progress: 15,
        courses: [
          {
            title: "Python for Data Science and Machine Learning",
            platform: "Udemy",
            duration: "44 hours",
            url: "https://www.udemy.com/course/python-for-data-science-and-machine-learning/",
          },
        ],
      },
      {
        name: "Machine Learning",
        current: "Beginner",
        target: "Advanced",
        progress: 5,
        courses: [
          {
            title: "Machine Learning Specialization",
            platform: "Coursera",
            duration: "80 hours",
            url: "https://www.coursera.org/specializations/machine-learning-introduction",
          },
          {
            title: "Hands-On Machine Learning",
            platform: "O'Reilly",
            duration: "60 hours",
            url: "https://www.oreilly.com/library/view/hands-on-machine-learning/9781098125967/",
          },
        ],
      },
      {
        name: "TensorFlow",
        current: "Beginner",
        target: "Intermediate",
        progress: 10,
        courses: [
          {
            title: "TensorFlow Developer Certificate",
            platform: "Coursera",
            duration: "50 hours",
            url: "https://www.coursera.org/professional-certificates/tensorflow-in-practice",
          },
        ],
      },
    ],
  },
  {
    id: "devops",
    rank: 3,
    title: "DevOps Engineer",
    description: "Automate infrastructure and streamline deployment pipelines",
    avgSalary: "6,750K EGP",
    growth: "+23%",
    matchScore: 0,
    skillGaps: [
      {
        name: "Docker",
        current: "Beginner",
        target: "Advanced",
        progress: 10,
        courses: [
          {
            title: "Docker & Kubernetes: The Complete Guide",
            platform: "Udemy",
            duration: "35 hours",
            url: "https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/",
          },
        ],
      },
      {
        name: "AWS",
        current: "Beginner",
        target: "Intermediate",
        progress: 5,
        courses: [
          {
            title: "AWS Certified Solutions Architect",
            platform: "Udemy",
            duration: "47 hours",
            url: "https://www.udemy.com/course/aws-certified-solutions-architect-associate/",
          },
          {
            title: "AWS Cloud Practitioner Essentials",
            platform: "AWS Training",
            duration: "12 hours",
            url: "https://aws.amazon.com/training/digital/aws-cloud-practitioner-essentials/",
          },
        ],
      },
      {
        name: "Kubernetes",
        current: "Beginner",
        target: "Intermediate",
        progress: 5,
        courses: [
          {
            title: "Kubernetes for the Absolute Beginners",
            platform: "Udemy",
            duration: "30 hours",
            url: "https://www.udemy.com/course/learn-kubernetes/",
          },
        ],
      },
    ],
  },
];
