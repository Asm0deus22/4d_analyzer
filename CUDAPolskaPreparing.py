from TokenUtils import Token

allowedVariables = ["x", "y", "z", "t"]

allowedFunctionsDim1 = [
    "sin", "cos", "tan", "asin", "acos", "atan",
    "sinpi", "cospi", "sinh", "cosh", "tanh",
    "asinh", "acosh", "atanh",
    "exp", "exp2", "exp10", "expm1",
    "log", "log2", "log10", "log1p", "logb",
    "sqrt", "cbrt", "rcbrt", "rsqrt",
    "ceil", "floor", "trunc", "round", "rint",
    "erf", "erfc", "erfinv", "erfcinv",
    "tgamma", "lgamma",
    "j0", "j1", "y0", "y1",
    "cyl_bessel_i0", "cyl_bessel_i1",
    "normcdf", "normcdfinv",
    "fabs", "ilogb", "isnan", "isinf", "isfinite", "signbit"
]
allowedFunctionsDim2 = [
    "atan2",
    "fmod",
    "remainder",
    "hypot",
    "rhypot",
    "fmax",
    "fmin",
    "fdim",
    "copysign",
    "ldexp",
    "nextafter",
    "jn",
    "yn"
]
allowedFunctionsDim3 = [
    "norm3d",
    "rnorm3d",
    "fma"
]
allowedFunctionsDim4 = [
    "norm4d",
    "rnorm4d"
]
def checkVariables(tokens):
    errors = []
    for token in tokens:
        if (token.type == Token.TokenType.FUNC_OPEN):
            found = False
            if (token.data in allowedFunctionsDim1):
                found = True
            elif (token.data in allowedFunctionsDim2):
                found = True
            elif (token.data in allowedFunctionsDim3):
                found = True
            elif (token.data in allowedFunctionsDim4):
                found = True
            elif (token.data in allowedVariables):
                found = True
            if not found:
                errors.append("Function not found: " + token.data)
        elif (token.type == Token.TokenType.ID):
            if (token.data not in allowedVariables):
                errors.append("Variable not found: " + token.data)
    return errors