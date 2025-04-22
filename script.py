import os
import re
import json
import requests
from bs4 import BeautifulSoup, Tag, NavigableString
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
    
    # First, try to find the project title specifically
    title_strong = soup.find('strong', string=lambda s: s and ('Project Title' in s))
    if title_strong:
        # Get the full title text including any numbers
        title_text = title_strong.get_text().strip()
        next_element = title_strong.next_sibling
        title_value = ""
        # Collect text until we hit a <br> tag or another <strong> tag
        while next_element and not (isinstance(next_element, Tag) and next_element.name == 'strong'):
            if isinstance(next_element, NavigableString):
                title_value += next_element.strip()
            elif next_element.name == 'br':
                break
            next_element = next_element.next_sibling
            
        # Clean up the title
        title_key = "project_title"
        if title_value:
            # Remove "Project Title:" or "Project Title #X:" from the beginning
            project_data[title_key] = re.sub(r'^Project Title(?:\s*#\d+)?:\s*', '', title_value).strip()
    
    # Extract each field from the HTML using regex
    for field in fields:
        # Skip project title as we handled it separately
        if field == "Project Title":
            continue
            
        pattern = re.compile(f"{field}:(.*?)(?=(?:{'|'.join(fields)}:)|$)", re.DOTALL)
        matches = re.findall(pattern, text)
        
        # If we found a match, clean it up and add it to our data
        if matches:
            # Make sure we're dealing with a string, not a tuple
            match_value = matches[0]
            if isinstance(match_value, tuple):
                match_value = ' '.join(filter(None, match_value))
            project_data[field.lower().replace(" ", "_")] = match_value.strip()
    
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
                    
                    # Handle numbered project titles 
                    if "Project Title" in key:
                        key = "Project Title"
                    
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
                        field_key = key.lower().replace(" ", "_")
                        
                        # For project_title, clean up any numbering format
                        if field_key == "project_title":
                            # Remove "Project Title:" or "Project Title #X:" from the beginning
                            value = re.sub(r'^Project Title(?:\s*#\d+)?:\s*', '', value).strip()
                        
                        project_data[field_key] = value.strip()
    
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
        print("Warning: Could not find 'entry-content' div in HTML")
        return []
    
    # Find all paragraphs that contain project titles
    projects = []
    paragraphs = entry_content.find_all('p')
    
    for p in paragraphs:
        # Check if this paragraph contains a project title (including numbered ones)
        title_tag = p.find('strong', string=lambda s: s and (
            'Project Title' in s or 
            re.search(r'Project Title\s*#\d+', s) is not None)
        )
        if title_tag:
            projects.append(str(p))
    
    # If no projects were found using the above method, try an alternative approach
    if not projects:
        # Try to split by Project Title pattern including numbered variants
        html_str = str(entry_content)
        
        # Look for both "Project Title:" and "Project Title #X:"
        project_sections = re.split(r'<p>\s*<strong>Project Title(?:\s*#\d+)?:', html_str)
        
        if len(project_sections) > 1:
            # Skip the first element if it doesn't contain a project
            for i, section in enumerate(project_sections[1:]):
                # Add back the opening tags and the Project Title strong tag
                projects.append(f"<p><strong>Project Title:{section}</p>")
                
    # If still no projects found, try another approach - maybe they're using different HTML structure
    if not projects:
        # Look for any paragraph with a strong tag - might be a different format
        for p in paragraphs:
            if p.find('strong'):
                projects.append(str(p))
                
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
        
        print(f"Fetching content from {source}")
        
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
    try:
        html_content, department = get_html_content(source)
        
        # Split the HTML into individual project sections
        project_sections = split_projects(html_content)
        
        if not project_sections:
            print(f"Warning: No project sections found in {source}")
            return []
            
        print(f"Found {len(project_sections)} potential projects in {source}")
        
        # Process each project section
        projects = []
        for i, section in enumerate(project_sections):
            try:
                project_data = extract_project_details(section)
                # Add the department if not already present
                if 'department' not in project_data:
                    project_data['department'] = department
                
                # If we couldn't extract a project title, this might not be a valid project
                if 'project_title' not in project_data or not project_data['project_title']:
                    print(f"Warning: No project title found in section {i+1}, skipping")
                    continue
                
                # Add source information
                project_data['source'] = source
                project_data['project_id'] = f"{department}_{i+1}"
                
                projects.append(project_data)
            except Exception as e:
                print(f"Error processing project {i+1} in {source}: {str(e)}")
        
        return projects
        
    except Exception as e:
        print(f"Error scraping {source}: {str(e)}")
        return []


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


def batch_scrape(urls: List[str], save_individual: bool = True) -> None:
    """
    Scrape multiple URLs and save results.
    
    Args:
        urls: List of URLs to scrape
        save_individual: Whether to save individual JSON files for each department
    """
    all_projects = []
    
    for url in urls:
        print(f"\n--- Processing {url} ---")
        projects = scrape_research_projects(url)
        
        # Extract department name from URL for the output file
        path_parts = urlparse(url).path.strip('/').split('/')
        department = path_parts[-1].replace('-', '_')
        
        # Add to combined results
        all_projects.extend(projects)
        
        # Optionally save individual department results
        if save_individual:
            output_file = f"./data/json/{department}_projects.json"
            save_to_json(projects, output_file)
    
    # Save combined results
    if all_projects:
        combined_output = "./data/json/all_projects.json"
        save_to_json(all_projects, combined_output)
        print(f"\nTotal projects scraped: {len(all_projects)}")
        print(f"All projects saved to: {combined_output}")
    else:
        print("\nNo projects were found across all departments.")


def main():
    """
    Main function to run the script from command line.
    """
    parser = argparse.ArgumentParser(description="Scrape research projects from HTML files or URLs.")
    parser.add_argument("--source", help="Path to the HTML file or URL to scrape (optional)")
    parser.add_argument("--output", "-o", help="Output JSON file path (optional)", default=None)
    parser.add_argument("--batch", "-b", action="store_true", help="Run batch scraping for all departments")
    
    args = parser.parse_args()
    
    # URLs from the README
    department_urls = [
        "https://www.eng.ufl.edu/graduate/current-students/undergraduate-research/research-projects/computer-and-information-science-and-engineering/",
        "https://www.eng.ufl.edu/graduate/current-students/undergraduate-research/research-projects/electrical-and-computer-engineering/",
        "https://www.eng.ufl.edu/graduate/current-students/undergraduate-research/research-projects/institute-for-excellence-in-engineering-education/"
    ]
    
    # Run batch mode (scrape all departments)
    if args.batch or not args.source:
        print("Running batch scraping for all departments...")
        batch_scrape(department_urls)
        return
    
    # Single source mode
    source = args.source
    
    # Determine if source is a URL or local file
    is_url = source.startswith('http')
    
    # Generate default output path if not provided
    if not args.output:
        if is_url:
            # Extract department name from URL
            path_parts = urlparse(source).path.strip('/').split('/')
            department = path_parts[-1].replace('-', '_')
        else:
            department = os.path.basename(source).replace('.html', '')
        
        args.output = f"./data/json/{department}_projects.json"
    
    # Scrape the projects
    projects = scrape_research_projects(source)
    
    # Save to JSON
    save_to_json(projects, args.output)


if __name__ == "__main__":
    main()