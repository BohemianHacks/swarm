import argparse
import sys
from googlesearch import search
from fake_useragent import UserAgent
import urllib.parse

def save_to_file(output_file, data):
    """
    Append data to the specified output file.
    
    Args:
        output_file (str): Path to the output file
        data (str): Data to be written to the file
    """
    try:
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(data + '\n')
    except IOError as e:
        print(f"Error writing to file {output_file}: {e}")

def create_dorks(domain):
    """
    Generate a dictionary of Google dork queries for the given domain.
    
    Args:
        domain (str): Target domain to generate dorks for
    
    Returns:
        dict: Dictionary of dork queries
    """
    dorks = {
        'Git Folders': f'site:{domain} intitle:"Index of" ".git"',
        'Backup Files': f'site:{domain} ext:bkp OR ext:backup OR ext:conf OR ext:old',
        'Exposed Documents': f'site:{domain} ext:doc OR ext:docx OR ext:pdf OR ext:xls OR ext:txt',
        'Confidential Documents': f'site:{domain} intitle:"confidential" OR intitle:"private"',
        'Configuration Files': f'site:{domain} ext:xml OR ext:conf OR ext:cnf OR ext:reg OR ext:inf',
        'Subdomains': f'site:{domain} -www',
        'PHP Errors': f'site:{domain} "PHP Fatal error" OR "PHP Warning"',
        'Login Pages': f'site:{domain} inurl:login OR inurl:admin OR inurl:dashboard',
        'Open Redirects': f'site:{domain} inurl:redirect OR inurl:redir OR inurl:out',
        'Cloud Buckets': f'site:{domain} inurl:amazonaws.com OR inurl:blob.core.windows.net',
        'LinkedIn Employees': f'site:linkedin.com "* at {domain}"'
    }
    return dorks

def perform_dork_search(domain, dorks, num_results):
    """
    Perform Google dork searches and display/save results.
    
    Args:
        domain (str): Target domain
        dorks (dict): Dictionary of dork queries
        num_results (int): Number of results per dork
        output_file (str, optional): File to save results
    """
    ua = UserAgent()
    
    for dork_name, dork_query in dorks.items():
        print(f"\n[+] Searching for {dork_name}:")
        try:
            # Encode the query to handle special characters
            encoded_query = urllib.parse.quote(dork_query)
            
            # Perform the search with a randomized user agent
            results = list(search(
                dork_query, 
                num_results=num_results, 
                user_agent=ua.random,
                advanced=True
            ))
            
            # Display and optionally save results
            if results:
                for idx, result in enumerate(results, 1):
                    result_str = f"{idx}. {result.url} - {result.title}"
                    print(result_str)
                    
                    # Save to output file if specified
                    if args.output:
                        save_to_file(args.output, f"{dork_name}: {result_str}")
            else:
                print(f"No results found for {dork_name}")
        
        except Exception as e:
            print(f"Error searching for {dork_name}: {e}")

def main():
    """
    Main function to coordinate Google dork search process.
    """
    # Validate domain input
    if not args.domain:
        print("Error: Domain is required. Use -d or --domain to specify.")
        sys.exit(1)
    
    # Generate and perform dork searches
    dorks = create_dorks(args.domain)
    perform_dork_search(args.domain, dorks, args.results)

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Google Dork Search Tool")
    parser.add_argument('-d', '--domain', required=True, help='Target domain to search')
    parser.add_argument('-r', '--results', type=int, default=10, 
                        help='Number of results per dork (default: 10)')
    parser.add_argument('-o', '--output', help='Output file to save results')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the main function
    main()
