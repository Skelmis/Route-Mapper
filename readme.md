Route Mapper
---

A pentest tool aimed at making source code assisted C# testing a little better.

**Problem Statement**
> I got given a C# code base and the webapp doesn't expose Swagger info and the code base doesn't build. What routes exist with what auth, and are any juicy?

---

*Yes, I got nerd snipped into making a proper tool instead of string manipulation + Regex.*

---

### Gotchas

- Everything is a string. It's in the source as `1`? Cool, now it's `"1"`. Types are hard and too complicated for this use-case.