import unittest

from linkedin_ats_resume import parse_linkedin_html, build_ats_resume


SAMPLE_HTML = """
<html>
  <head>
    <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": "Jane Doe",
        "jobTitle": "Software Engineer",
        "description": "Backend engineer with Python and cloud experience."
      }
    </script>
  </head>
  <body>
    <section>
      <h2>Experience</h2>
      <ul>
        <li>Senior Software Engineer at Acme Corp</li>
        <li>Software Engineer at Example Inc</li>
      </ul>
    </section>
    <section>
      <h2>Education</h2>
      <ul>
        <li>B.Sc. Computer Science, State University</li>
      </ul>
    </section>
    <section>
      <h2>Skills</h2>
      <ul>
        <li>Python</li>
        <li>Django</li>
      </ul>
    </section>
  </body>
</html>
"""


class TestResumeBuilder(unittest.TestCase):
    def test_parse_and_build_resume(self):
        profile = parse_linkedin_html(SAMPLE_HTML)
        self.assertEqual(profile["name"], "Jane Doe")
        self.assertEqual(profile["headline"], "Software Engineer")
        self.assertTrue(profile["skills"])

        resume = build_ats_resume(profile)
        self.assertIn("Jane Doe", resume)
        self.assertIn("Professional Summary", resume)
        self.assertIn("Experience", resume)


if __name__ == "__main__":
    unittest.main()
