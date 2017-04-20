## README
Take a list of unicode domains that look like reputable domains, e.g. https://www.ɡooɡⅼe.com vs https://www.google.com, and check whether they are already registered punycode domains.

A good way to generate a list would be using mimic: https://github.com/reinderien/mimic

```
# for i in $(seq 1 100); do echo -n companyname | mimic -m $i | base64 >> domain-list.txt; done
# cat domain-list.txt | sort | uniq > domain-list-uniq.txt
```