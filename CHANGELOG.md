# Change Log

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
