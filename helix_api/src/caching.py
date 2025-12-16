from typing import Any, Callable, TypeVar


class CacheManager:
    cache: dict[tuple, Any] = dict()
    T = TypeVar('T')

    def create_key(self, method_name: str, args: dict[str,str]) -> tuple:
        return (method_name,) + tuple([f"{k}={str(v)}" for k,v in args.items() ])

    def get_cached_or_execute(self, method_name: str, args: dict[str, Any], callable: Callable[..., T]) -> T:
        key = self.create_key(method_name=method_name, args=args)

        if key in self.cache:
            print("===ALREADY CACHED===")
            return self.cache[key]
        print("===NOT CACHED YET===")
        to_cache = callable(**args)
        self.cache[key] = to_cache
        return to_cache

    def reset(self):
        self.cache.clear()