import os
import re
import json
import requests
from bs4 import BeautifulSoup
import argparse
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse


def extract_project_details(project_html: str) -> Dict[str, Any]:
    """
    Extract project details from an HTML string representing a single project.
    
    Args:
        project_html: HTML string containing project information
        
    Returns:
        Dictionary with project details
    """
    soup = BeautifulSoup(project_html, 'html.parser')
    project_data = {}
    
    # Extract all text from the project HTML
    text = soup.get_text(strip=True)
    
    # Define the fields we want to extract
    fields = [
        "Project Title", "Department", "Faculty Mentor", "Ph.D. Student Mentor(s)",
        "Terms Available", "Student Level", "Prerequisites", "Credit", "Stipend", 
        "Application Requirements", "Application Deadline", "Website", "Project Description"
    ]
    
    # Extract each field from the HTML
    for field in fields:
        pattern = re.compile(f"{field}:(.*?)(?=(?:{field}:|$))", re.DOTALL)
        matches = re.findall(pattern, text)
        
        # If we found a match, clean it up and add it to our data
        if matches:
            project_data[field.lower().replace(" ", "_")] = matches[0].strip()
    
    # Attempt direct extraction using HTML structure
    paragraphs = soup.find_all('p')
    for p in paragraphs:
        text_content = p.get_text()
        for field in fields:
            if field in text_content:
                # Extract key-value pairs based on <strong> tags
                strong_tags = p.find_all('strong')
                for strong in strong_tags:
                    key = strong.get_text().replace(':', '').strip()
                    value = ""
                    next_element = strong.next_sibling
                    while next_element and not (hasattr(next_element, 'name') and next_element.name == 'strong'):
                        if hasattr(next_element, 'get_text'):
                            value += next_element.get_text()
                        elif isinstance(next_element, str):
                            value += next_element
                        if hasattr(next_element, 'next_sibling'):
                            next_element = next_element.next_sibling
                        else:
                            break
                    if key in fields:
                        project_data[key.lower().replace(" ", "_")] = value.strip()
    
    # Extract emails using a regex pattern
    emails = re.findall(r'[\w\.-]+@[\w\.-]+', str(soup))
    if emails:
        project_data['contact_email'] = emails[0]
    
    # Clean up any remaining HTML tags in text fields
    for key in project_data:
        if isinstance(project_data[key], str):
            # Remove HTML tags
            project_data[key] = re.sub(r'<[^>]+>', '', project_data[key])
            # Clean up multiple spaces and line breaks
            project_data[key] = re.sub(r'\s+', ' ', project_data[key]).strip()
    
    return project_data


def split_projects(html_content: str) -> List[str]:
    """
    Split the HTML content into individual project sections.
    
    Args:
        html_content: Full HTML content from the file
        
    Returns:
        List of HTML strings, each containing one project
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    entry_content = soup.find('div', class_='entry-content')
    
    if not entry_content:
        return []
    
    # Assuming each project is contained in a <p> tag
    projects = []
    paragraphs = entry_content.find_all('p')
    
    for p in paragraphs:
        # Check if this paragraph contains a project title
        if p.find('strong') and 'Project Title' in p.find('strong').get_text():
            projects.append(str(p))
    
    # If no projects were found using the above method, try an alternative approach
    if not projects:
        # Try to split by Project Title pattern
        html_str = str(entry_content)
        project_sections = re.split(r'<p>\s*<strong>Project Title', html_str)
        
        if len(project_sections) > 1:
            # Skip the first element if it doesn't contain a project
            for section in project_sections[1:]:
                projects.append(f"<p><strong>Project Title{section}</p>")
    
    return projects


def get_html_content(source: str) -> tuple:
    """
    Get HTML content either from a local file or a URL.
    
    Args:
        source: Path to local file or URL
        
    Returns:
        Tuple of (html_content, department_name)
    """
    # Check if the source is a URL
    if source.startswith('http'):
        # Get the department name from the URL
        path_parts = urlparse(source).path.strip('/').split('/')
        department = path_parts[-1].replace('-', '_')
        
        # Fetch the content from the URL
        response = requests.get(source)
        response.raise_for_status()  # Raise an exception for HTTP errors
        html_content = response.text
        
        return html_content, department
    else:
        # Read from local file
        with open(source, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Get department from filename
        department = os.path.basename(source).replace('.html', '')
        
        return html_content, department


def scrape_research_projects(source: str) -> List[Dict[str, Any]]:
    """
    Scrape research projects from the provided HTML file or URL.
    
    Args:
        source: Path to the HTML file or URL to scrape
        
    Returns:
        List of dictionaries containing project data
    """
    html_content, department = get_html_content(source)
    
    # Split the HTML into individual project sections
    project_sections = split_projects(html_content)
    
    # Process each project section
    projects = []
    for i, section in enumerate(project_sections):
        try:
            project_data = extract_project_details(section)
            # Add the department if not already present
            if 'department' not in project_data:
                project_data['department'] = department
            
            # Add source information
            project_data['source'] = source
            project_data['project_id'] = f"{department}_{i+1}"
            
            projects.append(project_data)
        except Exception as e:
            print(f"Error processing project {i+1} in {source}: {e}")
    
    return projects


def save_to_json(data: List[Dict[str, Any]], output_file: str) -> None:
    """
    Save the extracted data to a JSON file.
    
    Args:
        data: List of project dictionaries
        output_file: Path where the JSON file will be saved
    """
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved {len(data)} projects to {output_file}")


def main():
    """
    Main function to run the script from command line.
    """
    parser = argparse.ArgumentParser(description="Scrape research projects from HTML files or URLs.")
    parser.add_argument("source", help="Path to the HTML file or URL to scrape")
    parser.add_argument("--output", "-o", help="Output JSON file path", default=None)
    
    args = parser.parse_args()
    
    # Determine if source is a URL or local file
    is_url = args.source.startswith('http')
    
    # Generate default output path if not provided
    if not args.output:
        if is_url:
            # Extract department name from URL
            path_parts = urlparse(args.source).path.strip('/').split('/')
            department = path_parts[-1].replace('-', '_')
        else:
            department = os.path.basename(args.source).replace('.html', '')
        
        args.output = f"./data/json/{department}_projects.json"
    
    # Scrape the projects
    projects = scrape_research_projects(args.source)
    
    # Save to JSON
    save_to_json(projects, args.output)


if __name__ == "__main__":
    main()