Get the latest version of ANARCI

https://github.com/oxpig/ANARCI

https://bioconda.github.io/recipes/anarci/README.html


There's an offical image here:

``` 
docker pull quay.io/biocontainers/anarci:2024.05.21--pyhdfd78af_0
```

However we want to have as much version control as possible. Thus we build the image ourselves.
First, ensure you have the git submodule downloaded:

```
git submodule update --recursive
```

Next build the image. Ensure the working directory is the root of this repo.

```
docker build  -f anarci/Dockerfile -t anarci .
```

explore ANARCI from command line

```
docker run -it anarci ANARCI
```

Perform AA numbering on a fasta file:

```
docker run --volume=./test.fasta:/test.fasta:ro --volume=./anarci_output.txt:/anarci_output.txt -it anarci ANARCI -i test.fasta -o anarci_output.txt
```
