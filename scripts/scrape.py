
# Updated URL format for pages
SEARCH_URL: str = 'https://www.b9.com.br/shows/naruhodo/?pagina={}#anchor-tabs'

def get_podcast_posts(page_number: int) -> List[str]:
    print(f"get_podcast_posts called for page {page_number}", flush=True)
    """
    Retrieve podcast post URLs from a search page.

    This function formats the search URL with the provided page number,
    fetches the page content using get_soup, and extracts all post links
    that contain 'naruhodo' in their href using multiple selectors to ensure
    we catch all episodes. Only keeps links from b9.com.br domain.

    Args:
        page_number (int): The page number to scrape.

    Returns:
        List[str]: A list of URLs for the podcast posts found on the page.
    """
    # Format the URL with the given page number and retrieve its parsed content.
    soup = get_soup(SEARCH_URL.format(page_number))
    
    # Find all links using multiple selectors to catch all possible episode links
    all_links = []
    
    # Method 1: Direct link search
    links = soup.find_all('a', href=lambda href: href and 'naruhodo' in href.lower())
    all_links.extend(links)
    
    # Method 2: Search in article titles
    articles = soup.find_all('article')
    for article in articles:
        title_links = article.find_all('a', href=lambda href: href and 'naruhodo' in href.lower())
        all_links.extend(title_links)
    
    # Method 3: Search in post listings
    post_listings = soup.find_all('div', class_='post-listing')
    for listing in post_listings:
        listing_links = listing.find_all('a', href=lambda href: href and 'naruhodo' in href.lower())
        all_links.extend(listing_links)
    
    # Extract unique URLs while preserving order and add base URL if needed
    # Only keep URLs from b9.com.br domain
    seen = set()
    unique_links = []
    for link in all_links:
        href = link['href']
        # Add base URL if the link is relative
        if href.startswith('/'):
            href = f"https://www.b9.com.br{href}"
        
        # Only keep links from b9.com.br domain
        if (href not in seen and 
            'naruhodo' in href.lower() and 
            'b9.com.br' in href.lower() and
            not any(ext in href.lower() for ext in ['podcast.apple', 'facebook', 'twitter', 'spotify', 'youtube'])):
            seen.add(href)
            unique_links.append(href)
    
    print(f"Found {len(unique_links)} unique b9.com.br podcast links on page {page_number}", flush=True)
    return unique_links

# Updated to iterate from page 1 to 35
def scrape_references() -> List[List[str]]:
    print("scrape_references called", flush=True)
    """
    Scrape references from podcast posts across pages 1 to 35.

    Returns:
        List[List[str]]: A list of lists, where each inner list contains a post URL
                         and its corresponding references.
    """
    all_references: List[List[str]] = []
    
    # Iterate from page 1 to 35
    for page in range(21, 36):
        print(f"Scraping page {page} of 35...", flush=True)
        try:
            post_links = get_podcast_posts(page)
            
            # If no valid Naruhodo episodes are found, log and continue
            if not post_links:
                print(f"No Naruhodo episodes found on page {page}. Continuing to next page.")
                continue
            
            # Process each episode link
            for post_link in post_links:
                print(f"Scraping post {post_link}...", flush=True)
                try:
                    references = extract_references(post_link)
                    print(f"Extracted {len(references)} references from {post_link}", flush=True)
                    # Prepend the post URL to the list of references.
                    all_references.append([post_link] + references)
                    # Pause for 1-2 seconds to be respectful to the server.
                    time.sleep(random.uniform(1, 2))
                except Exception as e:
                    print(f"Error scraping {post_link}: {str(e)}", flush=True)
                    continue

        except Exception as e:
            print(f"Error processing page {page}: {str(e)}", flush=True)
            # Continue to the next page instead of breaking
            continue

    print(f"Scraping completed. Processed {len(all_references)} episodes.", flush=True)
    return all_references

def save_to_csv(data: List[List[str]], filename: str = 'references3.csv') -> None:
    print(f"save_to_csv called with {len(data)} rows", flush=True)
    """
    Save the scraped data to a CSV file with structured columns.
    Each reference will be in its own column (Reference_1, Reference_2, etc.).

    Args:
        data (List[List[str]]): List where each inner list contains [episode_url, reference1, reference2, ...]
        filename (str): Name of the output CSV file
    """
    # Find the maximum number of references in any episode
    max_refs = max(len(row) - 1 for row in data)  # -1 because first element is episode URL
    
    # Create column names
    columns = ['Episode'] + [f'Reference_{i+1}' for i in range(max_refs)]
    
    # Create a list of dictionaries where each dictionary represents a row
    structured_data = []
    for row in data:
        episode_data = {'Episode': row[0]}  # First element is always the episode URL
        
        # Add references to their respective columns
        for i, ref in enumerate(row[1:]):  # Skip the first element (episode URL)
            if ref.strip():  # Only add non-empty references
                episode_data[f'Reference_{i+1}'] = ref.strip()
        
        structured_data.append(episode_data)
    
    # Convert to DataFrame and save to CSV
    df = pd.DataFrame(structured_data, columns=columns)
    
    # Save to CSV, handling missing values properly
    df.to_csv(filename, index=False, encoding='utf-8')
    
    print(f"Saved {len(df)} episodes with up to {max_refs} references each to {filename}", flush=True)
    print(f"Column names: {', '.join(columns)}", flush=True)

if __name__ == "__main__":
    print("Main block started", flush=True)
    # Load environment variables from the .env file (if needed)
    load_dotenv()
    print("Loaded .env", flush=True)

    # Scrape references from the website and save them to a CSV file.
    references = scrape_references()
    print("scrape_references finished", flush=True)
    save_to_csv(references)
    print("Data has been saved to references.csv", flush=True)