from analyzer import get_domain_authority

da, pa = get_domain_authority("https://fortune.com/recommends/investing/best-bitcoin-ira-companies/")
print(f"Domain Authority: {da}, Page Authority: {pa}")