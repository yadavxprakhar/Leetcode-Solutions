const fs = require("fs");

function getProblems() {
  return fs.readdirSync(".").filter(
    (file) => fs.statSync(file).isDirectory() && file !== ".git"
  );
}

function generateTable(problems) {
  let table = "| Problem | Link |\n|--------|------|\n";

  problems.forEach((p) => {
    table += `| ${p} | [View](./${p}) |\n`;
  });

  return table;
}

function updateReadme(table) {
  let readme = fs.readFileSync("README.md", "utf-8");

  const newSection = `
<!-- START_TABLE -->
${table}
<!-- END_TABLE -->
`;

  readme = readme.replace(
    /<!-- START_TABLE -->[\s\S]*<!-- END_TABLE -->/,
    newSection
  );

  fs.writeFileSync("README.md", readme);
}

const problems = getProblems();
const table = generateTable(problems);
updateReadme(table);
