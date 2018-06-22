Like `npm pack`, but checks that all package.json `files` exist and tries to find `require`s missing from `files`.

This shouldn’t be run on untrusted packages. `prepack` and `postpack` scripts can be avoided with `npm pack --ignore-scripts`, but it’s possible there are other ways to convince `npm pack` to do something unsafe.


```sh
npm() {
    if [[ pack = "$1" ]]; then
        echo 'Use npm-pack-check instead' >&2
        return 1
    fi

    npm "$@"
}
```
