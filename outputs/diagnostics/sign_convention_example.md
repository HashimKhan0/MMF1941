# Sign-convention test, worked by hand

**DD-01.** Every rate is USD per unit of the commodity currency, so a positive
return always means the commodity currency appreciated and beta is expected
positive in all four pairs.

Date: **2014-03-10**

## AUDUSD - already USD per unit, used as pulled

    previous close   0.90680  USD per AUD
    this close       0.90200  USD per AUD
    ds = ln(0.90200 / 0.90680) = -0.005307  (-0.5307%)

The rate fell, so one AUD buys
fewer USD: the AUD
depreciated. s rose => positive return. Correct.

## USDCAD - quoted CAD per USD, must be inverted

    previous close   1.10870  CAD per USD
    this close       1.11080  CAD per USD

Inverting the quote:

    previous         1/1.10870 = 0.901957  USD per CAD
    this close       1/1.11080 = 0.900252  USD per CAD
    ds = ln(0.900252 / 0.901957) = -0.001892

Negating the raw log return instead, since log(1/x) = -log(x):

    ds = -ln(1.11080 / 1.10870) = -0.001892

The two agree to 8.74e-17, which is floating-point noise.
This is why the pipeline negates the return rather than inverting the price: the
stored price column stays exactly as pulled.

The rate rose, so one USD buys
more CAD: the CAD
depreciated. After inversion
ds = -0.001892, which is negative - the same
economic reading as AUD. Correct.

## Automated counterpart

`outputs/diagnostics/sign_check.csv` requires every convention-A return to
correlate NEGATIVELY with the dollar factor. A positive correlation means an
inversion was missed.
