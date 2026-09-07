# JOCKY Labs: Insight Engine

Prompt for Lovable: JOCKY Labs Website

Project Name: JOCKY Labs — Next-Gen Forensic Analysis Platform

Project Goal: To create a modern, professional, and functional website for "JOCKY Labs," a cybersecurity platform for stealthy computer and network forensics. The design should be inspired by the clean, trustworthy layout of cybercrestcompliance.com but with a dark, technical "cyber" aesthetic. The core user workflow is: Dashboard → Scripts → Agents → Operations → Results → Reports.

1. Visual Style & Design System

Core Aesthetic: Create a dark theme with a deep navy/dark gray background (e.g., #0B1124, #1E293B). The overall feel should be professional, high-tech, and security-focused, conveying stealth and precision.

Color Palette:

Accent Color: Use a vibrant cyan or electric blue (e.g., #00E5FF, #38BDF8) for primary buttons, highlights, and interactive elements.

Status Colors: Use a clean green (e.g., #10B981) for "Online" status, yellow/amber (e.g., #F59E0B) for "Warning" or "Executing", and red (e.g., #EF4444) for "Offline" or "Critical Alerts."

Text: Use white (#FFFFFF) or light gray (#94A3B8) for primary text on dark backgrounds to ensure readability.

Typography: Use a clean, modern sans-serif font for headings and body text (e.g., Inter or Roboto).

Layout: Implement a clean, card-based, grid layout (using CSS Grid or Flexbox) to organize information into digestible modules. Use ample spacing and subtle borders/backdrop blurs to separate sections.

2. Core User Workflow & Navigation

Primary Navigation: The main navigation should be a vertical sidebar on the left side of the application, containing the following main sections:

Dashboard

Agents

Scripts

Operations

Results

Reports

User Flow Emphasis: The UI should subtly guide the user through the core workflow. You can achieve this by:

Including a "Quick Actions" section on the Dashboard with buttons for Create Script, Deploy Script, and View Results.

Implementing a visual, context-aware workflow indicator at the top of relevant pages (e.g., [ Dashboard ] → [ Scripts ] → [ Agents ] → [ Deploy ]).

3. Page-by-Page Components & Features

3.1. Authentication (/login)

A clean, centered login page with fields for Email/Username and Password.

A "Forgot Password?" link.

A prominent Sign In button with the accent color.

3.2. Dashboard (/dashboard)

This is the main landing page. Include the following sections:

Hero / Welcome Section:

A headline: "Next-Gen Forensic Analysis. Zero Detection."

A System Status indicator (e.g., "All Systems Operational").

A prominent Stealth Mode Indicator toggle or badge (e.g., 🛡️ Stealth Mode: Active).

Quick Actions: Buttons for Create New Script, Deploy Script, and View Recent Results.

System Metrics (Cards): Display key metrics in a row of cards:

Total Agents: (e.g., 45)

Agents Online: (e.g., 42)

Active Operations: (e.g., 8)

Findings Summary: (e.g., 126 Alerts)

Recent Activity / Timeline (Chart): A small line or bar chart showing system activity over the past 24 hours.

Latest Findings (List): A scrollable list showing the most recent alerts or forensic findings with their severity (High, Medium, Low).

3.3. Scripts (/scripts)

Page Header: "Script Library" with a prominent + Create New Script button.

Script Editor View: A primary area with a code editor (e.g., using a library like react-simple-code-editor) featuring syntax highlighting for a custom language.

Script Details Panel (Sidebar or Area):

Input fields for Script Name, Description, and Category.

Target Selection: A section to select target agents (e.g., checkboxes for Agent-001, Agent-004).

Template Library (Sidebar): A collapsible sidebar on the right containing pre-built script templates (e.g., "Memory Scan", "Network Audit", "Registry Check").

Deployment Panel: A persistent footer or bottom section with a Deploy button and a progress indicator.

3.4. Agents (/agents)

Agent Overview (Stats): Top cards showing Total Agents, Online, Executing, Offline.

Agent List (Table): A detailed, sortable table with columns for: Agent ID, Hostname, OS, IP Address, Status (with color-coded indicator), Last Seen, and Current Task.

Agent Details (Modal or Split View): When an agent is clicked, display a detailed view containing:

System Information.

A Live Activity Log (a terminal-style box showing real-time commands/results).

Execution History.

Collected Data preview.

3.5. Results (/results)

Results Dashboard (Stats): Top cards summarizing Total Findings, Suspicious Activity, Open Ports, Critical Alerts.

Data Tabs: Use tabs to switch between different types of forensic data:

Overview: A high-level summary.

Registry Analysis: Display registry keys in a tree or list.

File System Analysis: A file explorer-like view.

Network Analysis: A table of active connections and open ports.

Process Analysis: A list of running processes with details.

Data Visualizations: Include a chart (e.g., a pie chart or bar graph) showing the distribution of findings by severity.

Action Button: A prominent Generate Report button.

3.6. Reports (/reports)

Generate Report Form: Options to select the Report Type (e.g., "Full Forensic Report," "Executive Summary"), Date Range, and Include Sections (e.g., Registry, Network).

Report Preview: A section to preview the generated report.

Export Options: Buttons for Export as PDF and Export as CSV.

Report History: A list of previously generated reports with dates and download links.

4. Important Components for the Prototype

Responsive Navigation: The sidebar should be collapsible on smaller screens (hamburger menu).

Interactive Elements: Focus on making the dashboard metrics, agent statuses, and script deployment flow interactive.

Visual Feedback: All user actions (e.g., deploying a script, clicking an agent) should have loading states, success toasts, or error notifications to make the prototype feel functional.

Stealth Mode Visual: Implement a visual indicator for "Stealth Mode" in the header or sidebar. This is a key differentiator for the project.

Polymorphism Notification: When a script is deployed, include a small animation or a log entry that shows the polymorphic engine changing the script's hash (e.g., Hash: a7f4... → 9e1b...).

5. Technology & Infrastructure (for Lovable)

Language: Use TypeScript for type safety and better code quality.

Framework: Use React or Next.js for a dynamic, component-based UI.

Styling: For a modern, utility-first approach, use Tailwind CSS. This will make it easy to implement the dark theme, color palette, and card-based layout.

Charts: Use a library like Chart.js (with a React wrapper like react-chartjs-2) for the data visualizations.

Icons: Use a professional icon set like Lucide React or Font Awesome.

Example Page Code Snippet (Conceptual)

This is a non-functional example of how you might describe a single page:

typescript

// Dashboard Page
const DashboardPage = () => {
  return (
    <div className="p-6 bg-dark-bg text-white min-h-screen">
      {/* Hero Section */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold">Next-Gen Forensic Analysis</h1>
        <p className="text-gray-400">Centralized Investigation Intelligence</p>
        <div className="mt-4 flex gap-4">
          <Button className="bg-cyan-500 text-black">Create Script</Button>
          <Button variant="outline">View Results</Button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <MetricCard title="Total Agents" value="42" />
        <MetricCard title="Online" value="38" />
        <MetricCard title="Active Operations" value="8" />
        <MetricCard title="Findings" value="126" />
      </div>

      {/* Activity & Findings */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ActivityChart />
        <RecentFindingsList />
      </div>
    </div>
  );
};

By using this prompt, Lovable will generate a robust, multi-page application that mirrors the structure and professional design of high-end cybersecurity platforms, effectively showcasing the JOCKY Labs concept.

This project was built with [Lovable](https://lovable.dev).

**Live app**: https://jocky-stealth-core.lovable.app

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/a3bc3424-c7eb-466c-9d9c-b4a6f3e374dc).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
