# Change Log

## v1.1.0 -- 2022-04-11
-----------------------
#### Features
* Support for Unit objects from `pint`.
* Support for classes with underlying `__slots__` objects.
* Support for classes that utilize `to_json()` and `from_json()`.
* Metadata arguments can be marked to be ignored when snapshotting.
#### Bug-Fixes
* Objects with `from_json()` are properly instantiated when comparing snapshots
* Objects of type `float` and `float64` are now properly compared
* Iterable objects and `numpy` iterable objects are now properly compared

## v1.0.1 -- 2021-03-26
-----------------------
#### Features
* Support for pathlib.Path objects.
#### Bug-Fixes
* Collections are now properly serialized by both
the `json.dump` and `json.dumps` methods.

## v1.0.0 -- 2021-02-01
-----------------------
#### Features
* Support of bytes objects
* Support of numpy arrays
* Support of pandas dataframes
#### Bug-Fixes
* Metadata for snapshots is now properly serialized.
* Recursive objects are handled (recursive parts are ignored).

## v0.2.0 (Beta) -- 2020-11-18
-----------------------
#### Features
* Human-Readable diff within assertion errors.
* SnappierShot summary at the end of `pytest` session.
* Support for the `decimal.Decimal` type added.
#### Bug-Fixes
* Custom-serialized collections were not being asserted properly.

## v0.1.0 (Beta) -- 2020-10-16
-----------------------
* Package published!
