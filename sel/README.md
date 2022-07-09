build & run

```bash
docker up
```

clean

```bash
docker rmi $(docker images -f "dangling=true" -q)
```